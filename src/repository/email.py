from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User


async def get_user_by_email( email: str, db: AsyncSession = Depends( get_db ) ):
	"""
	Return a user by email address.

	:param email: Email address to search for.
	:param db: Asynchronous database session.
	:return: User instance if found, otherwise None.
	"""
	stmt = select( User ).filter_by( email=email )
	user = await db.execute( stmt )
	user = user.scalar_one_or_none()
	return user


async def confirmed_email( email: str, db: AsyncSession = Depends( get_db ) ):
	"""
	Mark a user's email address as confirmed.

	:param email: Email address of the user.
	:param db: Asynchronous database session.
	:return: None.
	"""
	user = await get_user_by_email( email, db )
	user.confirmed = True
	await db.commit()
