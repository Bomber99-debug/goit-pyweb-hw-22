from pydantic import BaseModel, EmailStr, Field


class UserBaseSchema( BaseModel ):
	id: int
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	password: str = Field( min_length=6, max_length=20 )


class UserResponseSchema( BaseModel ):
	id: int
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	avatar: str | None

	class Config:
		from_attributes = True


class UserCreateSchema( BaseModel ):
	user_name: str = Field( min_length=3, max_length=255 )
	email: EmailStr
	password: str = Field( min_length=6, max_length=20 )
	avatar: str | None = Field( default=None )
