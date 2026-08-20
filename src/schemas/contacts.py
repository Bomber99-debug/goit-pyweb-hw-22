from datetime import date, datetime  # noqa: EXE002

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.user import UserResponseSchema


class PhoneBaseSchema( BaseModel ):
	"""Represent common phone number fields."""

	id: int
	number: str = Field( min_length=9, max_length=13 )
	contact_id: int


class PhoneCreateSchema( PhoneBaseSchema ):
	"""Represent data required to create a phone record."""

	...


class PhoneUpdateSchema( PhoneBaseSchema ):
	"""Represent data required to update a phone record."""

	...


class PhoneResponseSchema( PhoneBaseSchema ):
	"""Represent a phone record returned by the API."""

	model_config = ConfigDict( from_attributes=True )

	id: int
	user: UserResponseSchema
	# Override the field inherited from PhoneBaseSchema.
	# This keeps compatibility with phone numbers already stored in the database.
	number: str = Field( min_length=9, max_length=13 )


class ContactPhoneCreateSchema( BaseModel ):
	"""Represent a phone number supplied when creating a contact."""

	number: str = Field( min_length=9, max_length=13 )


class ContactBaseSchema( BaseModel ):
	"""Represent common contact fields."""

	id: int
	first_name: str = Field( min_length=3, max_length=50 )
	last_name: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	birthday: date
	notes: str | None = Field( default=None, max_length=1000 )


class ContactUpdateSchema( ContactBaseSchema ):
	"""Represent data required to update a contact."""

	...


class ContactResponseSchema( BaseModel ):
	"""Represent a contact returned by the API."""

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
	"""Represent data required to create a contact."""

	first_name: str = Field( min_length=3, max_length=50 )
	last_name: str = Field( min_length=3, max_length=50 )
	email: EmailStr
	birthday: date
	notes: str | None = Field( default=None, max_length=1000 )
	phones: list[ ContactPhoneCreateSchema ]
