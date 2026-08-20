from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Phone, User
from src.schemas.contacts import PhoneCreateSchema, PhoneUpdateSchema


async def get_phones( db: AsyncSession, user: User, skip: int = 0, limit: int = 100, ) -> Sequence[ Phone ]:
	"""Повертає список телефонних номерів з урахуванням пагінації."""

	statement = select( Phone ).filter_by( user=user ).offset( skip ).limit( limit )

	result = await db.execute( statement )

	return result.scalars().all()


async def get_phone_by_id( db: AsyncSession, user: User, phone_id: int, ) -> Phone | None:
	"""Повертає телефонний номер за його ідентифікатором."""

	statement = select( Phone ).filter_by( id=phone_id, user=user )
	result = await db.execute( statement )

	return result.scalar_one_or_none()


async def get_phone_by_number( db: AsyncSession, user: User, phone_number: str, ) -> Phone | None:
	"""Повертає телефонний номер за його наявності."""

	statement = select( Phone ).filter_by( number=phone_number, user=user )
	result = await db.execute( statement )

	return result.scalar_one_or_none()


async def create_phone( db: AsyncSession, user: User, phone_data: PhoneCreateSchema, ) -> Phone:
	"""Створює новий телефонний номер."""

	new_phone = Phone( **phone_data.model_dump( exclude_unset=True ), user=user, )

	db.add( new_phone )
	await db.commit()

	return new_phone


async def update_phone( db: AsyncSession, user: User, phone_data: PhoneUpdateSchema, phone_id: int, ) -> Phone | None:
	"""Оновлює телефонний номер за його ідентифікатором."""

	statement = select( Phone ).filter_by( id=phone_id, user=user )
	result = await db.execute( statement )

	phone_to_update = result.scalar_one_or_none()

	if phone_to_update:
		phone_to_update.number = phone_data.number
		phone_to_update.contact_id = phone_data.contact_id

		await db.commit()
		await db.refresh( phone_to_update )

	return phone_to_update


async def delete_phone( db: AsyncSession, user: User, phone_id: int, ) -> Phone | None:
	"""Видаляє телефонний номер за його ідентифікатором."""

	statement = select( Phone ).filter_by( id=phone_id, user=user )
	result = await db.execute( statement )

	phone_to_delete = result.scalar_one_or_none()

	if phone_to_delete:
		await db.delete( phone_to_delete )
		await db.commit()

	return phone_to_delete
