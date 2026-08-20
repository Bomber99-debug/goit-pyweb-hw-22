from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User


async def get_user_by_email( email: str, db: AsyncSession = Depends( get_db ) ):
	"""Повертає користувача за його електронною адресою."""
	stmt = select( User ).filter_by( email=email )
	user = await db.execute( stmt )
	user = user.scalar_one_or_none()
	return user


async def confirmed_email( email: str, db: AsyncSession = Depends( get_db ) ):
	"""Позначає електронну адресу користувача як підтверджену."""
	user = await get_user_by_email( email, db )
	user.confirmed = True
	await db.commit()
