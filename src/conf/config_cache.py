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
	Створює ключ кешу для пошукових запитів поточного користувача.

	:param func: Функція, результат якої кешується.
	:param namespace: Простір імен кешу.
	:param request: Поточний HTTP-запит.
	:param response: Поточна HTTP-відповідь.
	:param args: Позиційні аргументи функції.
	:param kwargs: Іменовані аргументи функції.
	:return: Унікальний ключ кешу для поточного користувача.
	"""
	current_user = kwargs.get( "current_user" )
	return (f"{namespace}:"
	        f"{func.__name__}:"
	        f"user:{current_user.id}")
