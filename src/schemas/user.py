from pydantic import BaseModel, EmailStr, Field


class UserBaseSchema( BaseModel ):
	"""Represent common user fields."""
	id: int
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	password: str = Field( min_length=6, max_length=20 )


class UserResponseSchema( BaseModel ):
	"""Represent user data returned by the API."""
	id: int
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	avatar: str | None

	class Config:
		from_attributes = True


class UserCreateSchema( BaseModel ):
	"""Represent data required to register a new user."""
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	password: str = Field( min_length=6, max_length=20 )
	avatar: str | None = Field( default=None )
