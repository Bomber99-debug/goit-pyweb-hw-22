import pickle
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pyrate_limiter import Duration, Limiter, Rate
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.redis import redis_client
from src.entity.models import Phone, User
from src.repository import phones as phones_repository
from src.schemas.contacts import (PhoneCreateSchema, PhoneResponseSchema, PhoneUpdateSchema)
from src.services.auth import auth_service
from src.services.rate_limiter import RateLimiter

router = APIRouter( prefix="/phone", tags=[ "phone" ], )


@router.get( "/",
             response_model=list[ PhoneResponseSchema ],
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def get_phones( limit: int = Query( default=10, ge=10, le=100 ),
                      offset: int = Query( default=0, ge=0 ),
                      db: AsyncSession = Depends( get_db ),
                      current_user: User = Depends( auth_service.get_current_user ), ) -> Sequence[ Phone ]:
	"""
	Return a paginated list of phone numbers for the authenticated user.

	Results may be loaded from or stored in Redis cache.

	:param limit: Maximum number of phone records to return.
	:param offset: Number of phone records to skip.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Sequence of phone records.
	:raises HTTPException: If phone records cannot be found.
	"""
	phone_list_cache = f"current_user:{current_user.id}:phones:limit:{limit}:offset:{offset}"
	phone_list = await redis_client.get( phone_list_cache )
	if phone_list is None:
		phone_list = await phones_repository.get_phones( db=db, skip=offset, limit=limit, user=current_user, )
		if phone_list is None:
			raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Phone not found", )
		await redis_client.set( phone_list_cache, pickle.dumps( phone_list ) )
		await redis_client.expire( name=phone_list_cache, time=60 )
	else:
		phone_list = pickle.loads( phone_list )

	return phone_list


@router.get( "/{phone_id}",
             response_model=PhoneResponseSchema,
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def get_phone_by_id( db: AsyncSession = Depends( get_db ),
                           phone_id: int = Path( ge=1 ),
                           current_user: User = Depends( auth_service.get_current_user ), ) -> Phone:
	"""
	Return a phone record by identifier.

	:param db: Asynchronous database session.
	:param phone_id: Identifier of the requested phone record.
	:param current_user: Currently authenticated user.
	:return: Requested phone record.
	:raises HTTPException: If the phone record does not exist.
	"""

	phone_id_cache = f"current_user:{current_user.id}:phone_id:{phone_id}"
	phone = await redis_client.get( phone_id_cache )
	if phone is None:
		phone = await phones_repository.get_phone_by_id( db=db, phone_id=phone_id, user=current_user, )
		if phone is None:
			raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Phone not found", )
		await redis_client.set( phone_id_cache, pickle.dumps( phone ) )
		await redis_client.expire( phone_id_cache, time=60 )
	else:
		phone = pickle.loads( phone )

	return phone


@router.post( "/",
              response_model=PhoneCreateSchema,
              status_code=status.HTTP_201_CREATED,
              dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def create_phone( phone_data: PhoneCreateSchema,
                        db: AsyncSession = Depends( get_db ),
                        current_user: User = Depends( auth_service.get_current_user ), ) -> Phone:
	"""
	Create a new phone record for the authenticated user.

	Relevant Redis cache entries are invalidated after creation.

	:param phone_data: Validated phone creation data.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Newly created phone record.
	:raises HTTPException: If the phone number already exists.
	"""

	phone = await phones_repository.get_phone_by_number( db=db, phone_number=phone_data.number, user=current_user, )
	if phone is not None:
		raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Phone already exists", )

	phone = await phones_repository.create_phone( db=db, phone_data=phone_data, user=current_user, )

	patterns = [ f"current_user:{current_user.id}:phones:*", f"current_user:{current_user.id}:contacts:*" ]
	async for key in redis_client.scan_iter( match=patterns, ):
		await redis_client.delete( key, )

	return phone


@router.put( "/{phone_id}",
             response_model=PhoneUpdateSchema,
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def update_phone( phone_data: PhoneUpdateSchema,
                        phone_id: int = Path( ge=1 ),
                        db: AsyncSession = Depends( get_db ),
                        current_user: User = Depends( auth_service.get_current_user ), ) -> Phone:
	"""
	Update an existing phone record.

	:param phone_data: Validated phone update data.
	:param phone_id: Identifier of the phone record to update.
	:param db: Asynchronous database session.
	:param current_user: Currently authenticated user.
	:return: Updated phone record.
	:raises HTTPException: If the phone number already exists or the record is not found.
	"""

	phone = await phones_repository.get_phone_by_number( db=db, phone_number=phone_data.number, user=current_user, )
	if phone is not None:
		raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Phone already exists", )

	phone = await phones_repository.update_phone( db=db, phone_data=phone_data, phone_id=phone_id, user=current_user, )

	if phone is None:
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Phone not found", )

	await redis_client.delete( f"current_user:{current_user.id}:phone_id:{phone_id}" )
	patterns = [ f"current_user:{current_user.id}:phones:*", f"current_user:{current_user.id}:contacts:*" ]
	for pattern in patterns:
		async for key in redis_client.scan_iter( match=pattern, ):
			await redis_client.delete( key, )

	return phone


@router.delete( "/{phone_id}",
                status_code=status.HTTP_204_NO_CONTENT,
                dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def delete_phone( db: AsyncSession = Depends( get_db ),
                        phone_id: int = Path( ge=1 ),
                        current_user: User = Depends( auth_service.get_current_user ), ) -> None:
	"""
	Delete a phone record belonging to the authenticated user.

	:param db: Asynchronous database session.
	:param phone_id: Identifier of the phone record to delete.
	:param current_user: Currently authenticated user.
	:return: None.
	"""
	await phones_repository.delete_phone( db=db, phone_id=phone_id, user=current_user )

	await redis_client.delete( f"current_user:{current_user.id}:phone_id:{phone_id}" )
	patterns = [ f"current_user:{current_user.id}:phones:*", f"current_user:{current_user.id}:contacts:*" ]
	for pattern in patterns:
		async for key in redis_client.scan_iter( match=pattern, ):
			await redis_client.delete( key, )
