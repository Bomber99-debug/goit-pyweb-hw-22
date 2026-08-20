from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.models import Contact, Phone, User
from src.schemas.contacts import ContactCreateSchema, ContactUpdateSchema


async def get_contacts( db: AsyncSession, user: User, skip: int = 0, limit: int = 100, ) -> Sequence[ Contact ]:
	"""Повертає список контактів з урахуванням пагінації."""

	statement = (
			select( Contact ).filter_by( user=user ).options( selectinload( Contact.phones ) ).offset( skip ).limit(
				limit, ))

	result = await db.execute( statement )

	return result.scalars().all()


async def get_contact_by_id( db: AsyncSession, user: User, contact_id: int, ) -> Contact | None:
	"""Повертає контакт за його ідентифікатором."""

	statement = (select( Contact ).filter_by( id=contact_id, user=user ).options( selectinload( Contact.phones ) ))

	result = await db.execute( statement )

	return result.scalar_one_or_none()


async def create_contact( db: AsyncSession, user: User, contact_data: ContactCreateSchema, ) -> Contact:
	"""Створює контакт разом із переданими номерами телефонів."""

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
	"""Оновлює контакт за його ідентифікатором."""

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
	"""Видаляє контакт за його ідентифікатором."""

	statement = select( Contact ).filter_by( id=contact_id, user=user )
	result = await db.execute( statement )

	contact_to_delete = result.scalar_one_or_none()

	if contact_to_delete:
		await db.delete( contact_to_delete )
		await db.commit()

	return contact_to_delete
