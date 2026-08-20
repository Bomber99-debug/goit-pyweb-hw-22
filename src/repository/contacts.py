from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.models import Contact, Phone, User
from src.schemas.contacts import ContactCreateSchema, ContactUpdateSchema


async def get_contacts( db: AsyncSession, user: User, skip: int = 0, limit: int = 100, ) -> Sequence[ Contact ]:
	"""
	Return a paginated list of contacts owned by the specified user.

	Phone relationships are loaded together with each contact.

	:param db: Asynchronous database session.
	:param user: User who owns the contacts.
	:param skip: Number of contacts to skip.
	:param limit: Maximum number of contacts to return.
	:return: Sequence of contacts belonging to the user.
	"""

	statement = (
			select( Contact ).filter_by( user=user ).options( selectinload( Contact.phones ) ).offset( skip ).limit(
					limit, ))

	result = await db.execute( statement )

	return result.scalars().all()


async def get_contact_by_id( db: AsyncSession, user: User, contact_id: int, ) -> Contact | None:
	"""
	Return a contact by its identifier.

	The contact is selected only if it belongs to the specified user.

	:param db: Asynchronous database session.
	:param user: User who owns the contact.
	:param contact_id: Identifier of the contact.
	:return: Contact instance if found, otherwise None.
	"""

	statement = (select( Contact ).filter_by( id=contact_id, user=user ).options( selectinload( Contact.phones ) ))

	result = await db.execute( statement )

	return result.scalar_one_or_none()


async def create_contact( db: AsyncSession, user: User, contact_data: ContactCreateSchema, ) -> Contact:
	"""
	Create and persist a new contact with its phone numbers.

	:param db: Asynchronous database session.
	:param user: User who owns the new contact.
	:param contact_data: Validated data used to create the contact.
	:return: Newly created contact.
	"""

	contact_fields = contact_data.model_dump( exclude={ "phones" } )
	phone_models = [ Phone( **phone_data.model_dump(), user=user ) for phone_data in contact_data.phones ]

	new_contact = Contact( **contact_fields, phones=phone_models, user=user, )

	db.add( new_contact )
	await db.commit()

	return new_contact


async def update_contact( db: AsyncSession,
                          user: User,
                          contact_data: ContactUpdateSchema,
                          contact_id: int, ) -> Contact | None:
	"""
	Update an existing contact owned by the specified user.

	:param db: Asynchronous database session.
	:param user: User who owns the contact.
	:param contact_data: Validated contact update data.
	:param contact_id: Identifier of the contact to update.
	:return: Updated contact if found, otherwise None.
	"""

	statement = select( Contact ).filter_by( id=contact_id, user=user )
	result = await db.execute( statement )

	contact_to_update = result.scalar_one_or_none()

	if contact_to_update:
		contact_to_update.first_name = contact_data.first_name
		contact_to_update.last_name = contact_data.last_name
		contact_to_update.email = contact_data.email
		contact_to_update.birthday = contact_data.birthday
		contact_to_update.notes = contact_data.notes

		await db.commit()
		await db.refresh( contact_to_update )

	return contact_to_update


async def delete_contact( db: AsyncSession, user: User, contact_id: int, ) -> Contact | None:
	"""
	Delete a contact owned by the specified user.

	:param db: Asynchronous database session.
	:param user: User who owns the contact.
	:param contact_id: Identifier of the contact to delete.
	:return: Deleted contact if found, otherwise None.
	"""

	statement = select( Contact ).filter_by( id=contact_id, user=user )
	result = await db.execute( statement )

	contact_to_delete = result.scalar_one_or_none()

	if contact_to_delete:
		await db.delete( contact_to_delete )
		await db.commit()

	return contact_to_delete
