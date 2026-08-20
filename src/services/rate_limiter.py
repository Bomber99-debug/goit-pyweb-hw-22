from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter as BaseRateLimiter


class RateLimiter( BaseRateLimiter ):
	"""Обмежує частоту HTTP-запитів до маршрутів API."""

	async def __call__( self, request: Request, response: Response, ):

		"""Перевіряє, чи дозволено виконати поточний запит."""
		rate_key = await self.identifier( request )
		success = await self.limiter.try_acquire_async( rate_key, blocking=False, )
		if not success:
			return await self.callback( request, response, )
