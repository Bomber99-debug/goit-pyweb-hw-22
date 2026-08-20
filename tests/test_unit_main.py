from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from main import (app,
                  check_contacts_database_connection,
                  check_phones_database_connection,
                  check_users_database_connection,
                  lifespan,
                  redis_client,
                  )


class TestMain( IsolatedAsyncioTestCase ):

	def setUp( self ):
		self.db = MagicMock()
		self.db.execute = AsyncMock()

		self.healthcheckers = [ (check_contacts_database_connection, "Contacts database connection is healthy",),
		                        (check_phones_database_connection, "Phones database connection is healthy",),
		                        (check_users_database_connection, "User database connection is healthy",),
		                        ]

	async def test_lifespan_initializes_redis_cache( self ):
		with (
			patch( "main.redis_client.ping",
			       new_callable=AsyncMock, ) as mock_ping, patch( "main.RedisBackend", ) as mock_redis_backend, patch(
				"main.FastAPICache.init", ) as mock_cache_init, ):
			backend = MagicMock()
			mock_redis_backend.return_value = backend

			async with lifespan( app, ):
				mock_ping.assert_awaited_once()

				mock_redis_backend.assert_called_once_with( redis_client, )

				mock_cache_init.assert_called_once_with( backend, prefix="fastapi-cache", )

	async def test_healthcheck_success( self ):
		query_result = MagicMock()
		query_result.fetchone.return_value = (1,
		                                      )

		self.db.execute.return_value = query_result

		for checker, expected_message in self.healthcheckers:
			with self.subTest( checker=checker.__name__, ):
				result = await checker( db=self.db, )

				self.assertEqual( result, { "message": expected_message,
				                            }, )

	async def test_healthcheck_no_result( self ):
		query_result = MagicMock()
		query_result.fetchone.return_value = None

		self.db.execute.return_value = query_result

		for checker, _ in self.healthcheckers:
			with self.subTest( checker=checker.__name__, ):
				with self.assertRaises( HTTPException, ) as error:
					await checker( db=self.db, )

				self.assertEqual( error.exception.status_code, 500, )

				self.assertEqual( error.exception.detail, "Database health check returned no result", )

	async def test_healthcheck_database_error( self ):
		self.db.execute.side_effect = RuntimeError( "Database unavailable", )

		with patch( "builtins.print", ) as mock_print:
			for checker, _ in self.healthcheckers:
				with self.subTest( checker=checker.__name__, ):
					with self.assertRaises( HTTPException, ) as error:
						await checker( db=self.db, )

					self.assertEqual( error.exception.status_code, 500, )

					self.assertEqual( error.exception.detail, "Unable to connect to the database", )

			self.assertEqual( mock_print.call_count, 3, )
