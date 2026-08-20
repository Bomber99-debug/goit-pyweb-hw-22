from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter as BaseRateLimiter


class RateLimiter( BaseRateLimiter ):
	"""Provide request rate limiting for API endpoints."""

	async def __call__( self, request: Request, response: Response, ):

		"""
		Check whether the current request is allowed by the rate limiter.

		:param request: Incoming HTTP request.
		:param response: HTTP response associated with the request.
		:return: Rate-limit callback result when the limit is exceeded, otherwise None.
		"""
		rate_key = await self.identifier( request )
		success = await self.limiter.try_acquire_async( rate_key, blocking=False, )
		if not success:
			return await self.callback( request, response, )
