from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.redis import redis_client
from src.routes import auth, contacts, email, phones, searchs


@asynccontextmanager
async def lifespan( app: FastAPI ):
	await redis_client.ping()
	# Start event
	FastAPICache.init( RedisBackend( redis_client ), prefix="fastapi-cache" )
	yield


app = FastAPI( lifespan=lifespan )

origins = [ "*" ]

app.add_middleware( CORSMiddleware,
                    allow_origins=origins,
                    allow_credentials=True,
                    allow_methods=[ "*" ],
                    allow_headers=[ "*" ], )

app.include_router( auth.router )
app.include_router( contacts.router )
app.include_router( email.router )
app.include_router( phones.router )
app.include_router( searchs.router )


@app.get( "/" )
async def get_root() -> dict[ str, str ]:
	"""Повертає повідомлення про доступність API."""
	return { "message": "Contacts API is running" }


@app.get( "/contacts_healthchecker" )
async def check_contacts_database_connection( db: AsyncSession = Depends( get_db ),  # noqa: B008
                                              ) -> dict[ str, str ]:
	"""Перевіряє доступність бази даних для маршрутів контактів."""

	try:
		query_result = await db.execute( text( "SELECT 1" ) )
		database_response = query_result.fetchone()

		if database_response is None:
			raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			                     detail="Database health check returned no result", )

		return { "message": "Contacts database connection is healthy",
		         }
	except Exception as error:
		print( error )

		raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		                     detail="Unable to connect to the database", )


@app.get( "/phone_healthchecker" )
async def check_phones_database_connection( db: AsyncSession = Depends( get_db ), ) -> dict[ str, str ]:
	"""Перевіряє доступність бази даних для маршрутів телефонів."""

	try:
		query_result = await db.execute( text( "SELECT 1" ) )
		database_response = query_result.fetchone()

		if database_response is None:
			raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			                     detail="Database health check returned no result", )

		return { "message": "Phones database connection is healthy",
		         }
	except Exception as error:
		print( error )

		raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		                     detail="Unable to connect to the database", )


@app.get( "/user_healthchecker" )
async def check_phones_database_connection( db: AsyncSession = Depends( get_db ), ) -> dict[ str, str ]:
	"""Перевіряє доступність бази даних для маршрутів користувачів."""

	try:
		query_result = await db.execute( text( "SELECT 1" ) )
		database_response = query_result.fetchone()

		if database_response is None:
			raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			                     detail="Database health check returned no result", )

		return { "message": "User database connection is healthy",
		         }
	except Exception as error:
		print( error )

		raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		                     detail="Unable to connect to the database", )
