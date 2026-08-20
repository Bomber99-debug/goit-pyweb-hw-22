from pydantic import BaseModel, EmailStr

class RequestEmail( BaseModel):
	"""Represent an email verification request."""
	email: EmailStr