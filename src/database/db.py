import contextlib
from collections.abc import AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from src.conf.config import config


class DatabaseSessionManager:
	"""
	Manage the asynchronous database engine and SQLAlchemy sessions.
	"""

	def __init__( self, database_url: str ) -> None:
		self._engine: AsyncEngine = create_async_engine( database_url )
		self._session_factory: async_sessionmaker[ AsyncSession ] = (
				async_sessionmaker( bind=self._engine, autoflush=False, autocommit=False, expire_on_commit=False, ))

	@contextlib.asynccontextmanager
	async def session( self ) -> AsyncIterator[ AsyncSession ]:
		"""
		Create and manage an asynchronous database session.

		The session is automatically closed after use. Database integrity
		and SQLAlchemy errors are converted to appropriate HTTP errors.

		:return: Asynchronous database session.
		:raises RuntimeError: If the session factory is not initialized.
		:raises HTTPException: If a database integrity or SQLAlchemy error occurs.
		"""

		if self._session_factory is None:
			raise RuntimeError( "Session factory is not initialized" )

		database_session = self._session_factory()

		try:
			yield database_session
		except IntegrityError as error:
			print( error )
			raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Conflict", )
		except SQLAlchemyError as error:
			print( error )
			raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR )
		except Exception as error:
			print( error )
			await database_session.rollback()
			raise error
		finally:
			await database_session.close()


session_manager = DatabaseSessionManager( config.DB_URL )


async def get_db() -> AsyncIterator[ AsyncSession ]:
	"""
	Provide an asynchronous database session as a FastAPI dependency.

	:return: Asynchronous SQLAlchemy session.
	"""

	async with session_manager.session() as database_session:
		yield database_session
