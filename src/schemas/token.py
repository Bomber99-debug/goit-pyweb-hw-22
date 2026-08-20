from pydantic import BaseModel

class TokenShema( BaseModel ):
	"""Represent access and refresh tokens returned after authentication."""
	access_token: str
	refresh_token: str
	token_type: str = "bearer"