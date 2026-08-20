from pydantic import BaseModel

class TokenShema( BaseModel ):
	access_token: str
	refresh_token: str
	token_type: str = "bearer"