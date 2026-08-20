from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserCreateSchema


async def get_user_by_email( email: str, db: AsyncSession = Depends( get_db ) ):
	stmt = select( User ).filter_by( email=email )
	user = await db.execute( stmt )
	user = user.scalar_one_or_none()
	return user


async def create_user( body: UserCreateSchema, db: AsyncSession = Depends( get_db ) ):
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
	user.refresh_token = token
	await db.commit()


async def update_avatar( email, url: str, db: AsyncSession = Depends( get_db ) ) -> User | None:
	user = await get_user_by_email( email, db )
	user.avatar = url
	await db.commit()
	return user
