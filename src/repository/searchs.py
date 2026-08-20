from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.models import Contact, User


async def search_contacts( db: AsyncSession, user: User, query: str, ) -> Sequence[ Contact ]:
	"""Шукає контакти за ім'ям, прізвищем або електронною адресою."""

	statement = (
			select( Contact ).filter_by( user=user ).options( selectinload( Contact.phones ) ).where( or_(
				Contact.first_name.ilike(
				f"%{query}%", ), Contact.last_name.ilike( f"%{query}%" ), Contact.email.ilike( f"%{query}%" ), ), ))

	result = await db.execute( statement )

	return result.scalars().all()


async def get_contacts_with_upcoming_birthdays( db: AsyncSession, user: User, ) -> Sequence[ Contact ]:
	"""Повертає контакти, день народження яких припадає на найближчі дні."""

	current_date = date.today()
	upcoming_dates = [ current_date + timedelta( days=day_offset ) for day_offset in range( 8 ) ]
	upcoming_month_days = [ upcoming_date.strftime( "%m-%d" ) for upcoming_date in upcoming_dates ]

	statement = (select( Contact ).filter_by( user=user ).options( selectinload( Contact.phones ) ).where(
		func.to_char(
		Contact.birthday,
		"MM-DD", ).in_( upcoming_month_days, ), ))

	result = await db.execute( statement )

	return result.scalars().all()
