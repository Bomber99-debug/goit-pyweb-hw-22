import pickle
from collections.abc import Sequence

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request, status
from pyrate_limiter import Duration, Limiter, Rate
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.redis import redis_client
from src.entity.models import Contact, User
from src.repository import contacts as contact_repository, phones as phones_repository
from src.schemas.contacts import ContactCreateSchema, ContactResponseSchema, ContactUpdateSchema
from src.services.auth import auth_service
from src.services.email import send_email_add_contact
from src.services.rate_limiter import RateLimiter

router = APIRouter( prefix="/contacts", tags=[ "contacts" ], )


@router.get( "/",
             response_model=list[ ContactResponseSchema ],
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def get_contacts( limit: int = Query( default=10, ge=10, le=100 ),
                        offset: int = Query( default=0, ge=0 ),
                        db: AsyncSession = Depends( get_db ),
                        current_user: User = Depends( auth_service.get_current_user ), ) -> Sequence[ Contact ]:
	"""
	Return a paginated list of contacts for the authenticated user.

	Results are cached in Redis for a short period.

	:param limit: Maximum number of contacts to return.
	:param offset: Number of contacts to skip.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Sequence of contacts.
	:raises HTTPException: If contacts cannot be found.
	"""
	contact_list_cache = f"current_user:{current_user.id}:contacts:limit:{limit}:offset:{offset}"
	contact_list = await redis_client.get( contact_list_cache )
	if contact_list is None:
		contact_list = await contact_repository.get_contacts( db=db, skip=offset, limit=limit, user=current_user, )
		if contact_list is None:
			raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found", )
		await redis_client.set( contact_list_cache, pickle.dumps( contact_list ) )
		await redis_client.expire( name=contact_list_cache, time=60 )
	else:
		contact_list = pickle.loads( contact_list )

	return contact_list


@router.get( "/{contact_id}",
             response_model=ContactResponseSchema,
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def get_contact_by_id( db: AsyncSession = Depends( get_db ),
                             contact_id: int = Path( ge=1 ),
                             current_user: User = Depends( auth_service.get_current_user ), ) -> Contact:
	"""
	Return a contact by identifier for the authenticated user.

	The contact may be loaded from Redis cache.

	:param db: Asynchronous database session.
	:param contact_id: Identifier of the requested contact.
	:param current_user: Currently authenticated user.
	:return: Requested contact.
	:raises HTTPException: If the contact does not exist.
	"""
	contact_id_cache = f"current_user:{current_user.id}:contact_id:{contact_id}"
	contact = await redis_client.get( contact_id_cache )
	if contact is None:
		contact = await contact_repository.get_contact_by_id( db=db, contact_id=contact_id, user=current_user, )
		if contact is None:
			raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found", )
		await redis_client.set( contact_id_cache, pickle.dumps( contact ) )
		await redis_client.expire( contact_id_cache, time=60 )
	else:
		contact = pickle.loads( contact )
	return contact


@router.post( "/",
              response_model=ContactCreateSchema,
              status_code=status.HTTP_201_CREATED,
              dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def create_contact( contact_data: ContactCreateSchema,
                          bt: BackgroundTasks,
                          request: Request,
                          db: AsyncSession = Depends( get_db ),  # noqa: B008
                          current_user: User = Depends( auth_service.get_current_user ),  # noqa: B008
                          ) -> Contact:
	"""
	Create a new contact for the authenticated user.

	Phone numbers are checked for duplicates before creation. Related
	contact caches are invalidated and an email notification is scheduled.

	:param contact_data: Validated contact creation data.
	:param bt: FastAPI background task manager.
	:param request: Current HTTP request.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Newly created contact.
	:raises HTTPException: If one of the phone numbers already exists.
	"""

	for phone_data in contact_data.phones:
		phone = await phones_repository.get_phone_by_number( db=db, phone_number=phone_data.number,
		                                                     user=current_user, )
		if phone is not None:
			raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Phone already exists", )

	contact = await contact_repository.create_contact( db=db, contact_data=contact_data, user=current_user, )
	pattern = f"current_user:{current_user.id}:contacts:*"

	async for key in redis_client.scan_iter( match=pattern ):
		await redis_client.delete( key )
	bt.add_task( send_email_add_contact,
	             email_user=current_user.email,
	             user_name=current_user.user_name,
	             email_contact=contact_data.email,
	             first_name=contact_data.first_name,
	             last_name=contact_data.last_name,
	             phones=contact_data.phones, )
	return contact


@router.put( "/{contact_id}",
             response_model=ContactUpdateSchema,
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def update_contact( contact_data: ContactUpdateSchema,
                          contact_id: int = Path( ge=1 ),
                          db: AsyncSession = Depends( get_db ),  # noqa: B008
                          current_user: User = Depends( auth_service.get_current_user ),  # noqa: B008
                          ) -> Contact:
	"""
	Update an existing contact for the authenticated user.

	Relevant Redis cache entries are invalidated after the update.

	:param contact_data: Validated contact update data.
	:param contact_id: Identifier of the contact to update.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Updated contact.
	:raises HTTPException: If the contact does not exist.
	"""

	contact = await contact_repository.update_contact( db=db,
	                                                   contact_data=contact_data,
	                                                   contact_id=contact_id,
	                                                   user=current_user, )

	if contact is None:
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found", )

	await redis_client.delete( f"current_user:{current_user.id}:contact_id:{contact_id}" )
	patterns = [ f"current_user:{current_user.id}:phones:*", f"current_user:{current_user.id}:contacts:*" ]
	async for key in redis_client.scan_iter( match=patterns ):
		await redis_client.delete( key )

	return contact


@router.delete( "/{contact_id}",
                status_code=status.HTTP_204_NO_CONTENT,
                dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def delete_contact( db: AsyncSession = Depends( get_db ),
                          contact_id: int = Path( ge=1 ),
                          current_user: User = Depends( auth_service.get_current_user ), ) -> None:
	"""
	Delete a contact belonging to the authenticated user.

	Related Redis cache entries are invalidated after deletion.

	:param db: Asynchronous database session.
	:param contact_id: Identifier of the contact to delete.
	:param current_user: Currently authenticated user.
	:return: None.
	"""
	await contact_repository.delete_contact( db=db, contact_id=contact_id, user=current_user, )

	await redis_client.delete( f"current_user:{current_user.id}:contact_id:{contact_id}" )
	patterns = [ f"current_user:{current_user.id}:phones:*", f"current_user:{current_user.id}:contacts:*" ]
	async for key in redis_client.scan_iter( match=patterns ):
		await redis_client.delete( key )
