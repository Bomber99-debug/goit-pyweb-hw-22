from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserCreateSchema


async def get_user_by_email( email: str, db: AsyncSession = Depends( get_db ) ):
	"""
	Find a user by email address.

	:param email: Email address of the requested user.
	:param db: Asynchronous database session.
	:return: User instance if found, otherwise None.
	"""
	stmt = select( User ).filter_by( email=email )
	user = await db.execute( stmt )
	user = user.scalar_one_or_none()
	return user


async def create_user( body: UserCreateSchema, db: AsyncSession = Depends( get_db ) ):
	"""
	Create and persist a new user.

	If an avatar is not provided, the function attempts to generate
	one using Gravatar.

	:param body: User registration data.
	:param db: Asynchronous database session.
	:return: Newly created user.
	"""
	if body.avatar is None or body.avatar == "":
		avatar = None
		try:
			g = Gravatar( body.email )
			avatar = g.get_image()
			body.avatar = avatar
		except Exception as e:  # noqa: BLE001
			print( e )
			body.avatar = avatar

	new_user = User( **body.model_dump() )

	db.add( new_user )
	await db.commit()
	await db.refresh( new_user )
	return new_user


async def update_token( user: User, token: str | None, db: AsyncSession = Depends( get_db ) ):
	"""
	Update the user's refresh token.

	:param user: User whose token should be updated.
	:param token: New refresh token or None.
	:param db: Asynchronous database session.
	:return: None.
	"""
	user.refresh_token = token
	await db.commit()


async def update_avatar( email, url: str, db: AsyncSession = Depends( get_db ) ) -> User | None:
	"""
	Update the avatar URL for a user.

	:param email: Email address of the user.
	:param url: New avatar URL.
	:param db: Asynchronous database session.
	:return: Updated user instance.
	"""
	user = await get_user_by_email( email, db )
	user.avatar = url
	await db.commit()
	return user
