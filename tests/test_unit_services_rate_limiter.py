from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from src.services.rate_limiter import RateLimiter


class TestRateLimiter( IsolatedAsyncioTestCase ):

	def setUp( self ):
		self.request = MagicMock()
		self.response = MagicMock()

		self.base_limiter = MagicMock()

		self.rate_limiter = RateLimiter( limiter=self.base_limiter, )

		self.rate_limiter.identifier = AsyncMock( return_value="test-rate-key", )

		self.rate_limiter.callback = AsyncMock( return_value={ "detail": "Rate limit exceeded",
				}, )

		self.base_limiter.try_acquire_async = AsyncMock()

	async def test_request_allowed( self ):
		self.base_limiter.try_acquire_async.return_value = True

		result = await self.rate_limiter( self.request, self.response, )

		self.assertIsNone( result, )

		self.rate_limiter.identifier.assert_awaited_once_with( self.request, )

		self.base_limiter.try_acquire_async.assert_awaited_once_with( "test-rate-key", blocking=False, )

		self.rate_limiter.callback.assert_not_awaited()

	async def test_request_rejected( self ):
		self.base_limiter.try_acquire_async.return_value = False

		result = await self.rate_limiter( self.request, self.response, )

		self.assertEqual( result, { "detail": "Rate limit exceeded",
				}, )

		self.rate_limiter.callback.assert_awaited_once_with( self.request, self.response, )
