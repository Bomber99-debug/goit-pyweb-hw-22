import contextlib
from collections.abc import AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from src.conf.config import config


class DatabaseSessionManager:
	"""Керує асинхронним підключенням і сесіями бази даних."""

	def __init__( self, database_url: str ) -> None:
		self._engine: AsyncEngine = create_async_engine( database_url )
		self._session_factory: async_sessionmaker[ AsyncSession ] = (
				async_sessionmaker( bind=self._engine, autoflush=False, autocommit=False, expire_on_commit=False, ))

	@contextlib.asynccontextmanager
	async def session( self ) -> AsyncIterator[ AsyncSession ]:
		"""Створює сесію та закриває її після завершення роботи."""

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
	"""Надає сесію бази даних як залежність FastAPI."""

	async with session_manager.session() as database_session:
		yield database_session
