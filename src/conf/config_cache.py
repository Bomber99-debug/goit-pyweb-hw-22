from typing import Any, Callable, Dict, Optional, Tuple

from fastapi.requests import Request
from fastapi.responses import Response


def custom_search_key_builder( func: Callable[ ..., Any ],
                               namespace: str = "",
                               *,
                               request: Optional[ Request ] = None,
                               response: Optional[ Response ] = None,
                               args: Tuple[ Any, ... ],
                               kwargs: Dict[ str, Any ], ) -> str:
	"""
	Build a cache key for search requests of the current user.

	:param func: Function whose result is being cached.
	:param namespace: Cache namespace.
	:param request: Current HTTP request.
	:param response: Current HTTP response.
	:param args: Positional arguments passed to the cached function.
	:param kwargs: Keyword arguments passed to the cached function.
	:return: Cache key unique to the current user and cached function.
	"""
	current_user = kwargs.get( "current_user" )
	return (f"{namespace}:"
	        f"{func.__name__}:"
	        f"user:{current_user.id}")
