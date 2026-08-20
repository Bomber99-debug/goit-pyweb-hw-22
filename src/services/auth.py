import pickle
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.db import get_db
from src.database.redis import redis_client
from src.repository import users as users_repository


class Auth:
	pwd_context = CryptContext( schemes=[ "bcrypt" ], deprecated="auto" )
	SECRET_KEY = config.SECRET_KEY_JWT
	ALGORITHM = config.ALGORITHM

	def verify_password( self, plain_password, hashed_password ):
		return self.pwd_context.verify( plain_password, hashed_password )

	def get_password_hash( self, password: str ):
		return self.pwd_context.hash( password )

	oauth2_scheme = OAuth2PasswordBearer( tokenUrl="auth/login" )

	# define a function to generate a new access token
	async def create_access_token( self, data: dict, expires_delta: Optional[ float ] = None, ):
		to_encode = data.copy()
		if expires_delta:
			expire = datetime.now( timezone.utc ) + timedelta( seconds=expires_delta )
		else:
			expire = datetime.now( timezone.utc ) + timedelta( minutes=15 )
		to_encode.update( { "iat": datetime.now( timezone.utc ), "exp": expire, "scope": "access_token" }, )
		encoded_access_token = jwt.encode( to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM, )
		return encoded_access_token

	# define a function to generate a new refresh token
	async def create_refresh_token( self, data: dict, expires_delta: Optional[ float ] = None, ):
		to_encode = data.copy()
		if expires_delta:
			expire = datetime.now( timezone.utc ) + timedelta( seconds=expires_delta )
		else:
			expire = datetime.now( timezone.utc ) + timedelta( days=7 )
		to_encode.update( { "iat": datetime.now( timezone.utc ), "exp": expire, "scope": "refresh_token" }, )
		encoded_refresh_token = jwt.encode( to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM, )
		return encoded_refresh_token

	async def decode_refresh_token( self, refresh_token: str ):
		try:
			payload = jwt.decode( refresh_token, self.SECRET_KEY, algorithms=[ self.ALGORITHM ], )
			if payload[ "scope" ] == "refresh_token":
				email = payload[ "sub" ]
				return email
			raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token", )
		except JWTError:
			raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", )

	async def get_current_user( self, token: str = Depends( oauth2_scheme ), db: AsyncSession = Depends( get_db ), ):
		credentials_exception = HTTPException( status_code=status.HTTP_401_UNAUTHORIZED,
		                                       detail="Could not validate credentials",
		                                       headers={ "WWW-Authenticate": "Bearer" }, )

		try:
			# Decode JWT
			payload = jwt.decode( token, self.SECRET_KEY, algorithms=[ self.ALGORITHM ] )
			if payload[ "scope" ] == "access_token":
				email = payload[ "sub" ]
				if email is None:
					raise credentials_exception
			else:
				raise credentials_exception
		except JWTError as e:
			raise credentials_exception

		""" saving the user cache """
		user_name_cache = f"{payload[ "scope" ]}:{email}"
		user = await redis_client.get( user_name_cache )
		if user is None:
			user = await users_repository.get_user_by_email( email=email, db=db )
			if user is None:
				raise credentials_exception
			await redis_client.set( user_name_cache, pickle.dumps( user ) )
			await redis_client.expire( name=user_name_cache, time=900 )
		else:
			user = pickle.loads( user )

		return user

	def create_email_token( self, data: dict ):
		to_encode = data.copy()
		expire = datetime.now( timezone.utc ) + timedelta( days=1 )
		to_encode.update( { "iat": datetime.now( timezone.utc ), "exp": expire } )
		token = jwt.encode( to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM )
		return token

	async def get_email_from_token( self, token: str ):
		try:
			payload = jwt.decode( token, self.SECRET_KEY, algorithms=[ self.ALGORITHM ] )
			email = payload[ "sub" ]
			return email
		except JWTError as e:
			print( e )
			raise HTTPException( status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			                     detail="Invalid token for email verification", )


auth_service = Auth()
