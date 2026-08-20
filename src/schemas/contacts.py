from datetime import date, datetime  # noqa: EXE002

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.user import UserResponseSchema


class PhoneBaseSchema( BaseModel ):
	"""Базові дані телефонного номера."""

	id: int
	number: str = Field( min_length=9, max_length=13 )
	contact_id: int


class PhoneCreateSchema( PhoneBaseSchema ):
	"""Дані для створення окремого телефонного номера."""

	...


class PhoneUpdateSchema( PhoneBaseSchema ):
	"""Дані для оновлення телефонного номера."""

	...


class PhoneResponseSchema( PhoneBaseSchema ):
	"""Дані телефонного номера у відповіді API."""

	model_config = ConfigDict( from_attributes=True )

	id: int
	user: UserResponseSchema
	# Перевизначає поле з PhoneBaseSchema без перевірки довжини.
	# Це потрібно для старих номерів у базі, наприклад "string".
	number: str = Field( min_length=9, max_length=13 )


class ContactPhoneCreateSchema( BaseModel ):
	"""Номер телефону під час створення контакту."""

	number: str = Field( min_length=9, max_length=13 )


class ContactBaseSchema( BaseModel ):
	"""Базові дані контакту."""

	id: int
	first_name: str = Field( min_length=3, max_length=50 )
	last_name: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	birthday: date
	notes: str | None = Field( default=None, max_length=1000 )


class ContactUpdateSchema( ContactBaseSchema ):
	"""Дані для оновлення контакту."""

	...


class ContactResponseSchema( BaseModel ):
	"""Дані контакту у відповіді API."""

	model_config = ConfigDict( from_attributes=True )

	id: int
	first_name: str = Field( min_length=3, max_length=50 )
	last_name: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	birthday: date
	notes: str | None = Field( default=None, max_length=1000 )
	phones: list[ PhoneResponseSchema ]
	created_at: datetime
	updated_at: datetime
	user: UserResponseSchema


class ContactCreateSchema( BaseModel ):
	"""Дані для створення контакту."""

	first_name: str = Field( min_length=3, max_length=50 )
	last_name: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	birthday: date
	notes: str | None = Field( default=None, max_length=1000 )
	phones: list[ ContactPhoneCreateSchema ]
