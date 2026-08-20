from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config_cache import custom_search_key_builder
from src.database.db import get_db
from src.entity.models import Contact, User
from src.repository import searchs as search_repository
from src.schemas.contacts import ContactResponseSchema
from src.services.auth import auth_service

router = APIRouter( prefix="/searchs", tags=[ "search" ], )


@router.get( "/", response_model=list[ ContactResponseSchema ] )
@cache( expire=60, namespace="search", key_builder=custom_search_key_builder )
async def search_contacts( query: Annotated[
	str, Query( min_length=1, max_length=250, description="Ім'я, прізвище або електронна адреса контакту", ), ],
                           db: AsyncSession = Depends( get_db ),
                           current_user: User = Depends( auth_service.get_current_user ), ) -> Sequence[ Contact ]:
	"""Шукає контакти за ім'ям, прізвищем або електронною адресою."""

	contacts = await search_repository.search_contacts( db=db, query=query, user=current_user, )

	return contacts


@router.get( "/birthday/", response_model=list[ ContactResponseSchema ] )
@cache( expire=60, namespace="birthday", key_builder=custom_search_key_builder )
async def get_contacts_with_upcoming_birthdays( db: AsyncSession = Depends( get_db ),
                                                current_user: User = Depends( auth_service.get_current_user ), ) -> \
		Sequence[ Contact ]:
	"""Повертає контакти з днями народження у найближчому періоді."""

	contacts = await search_repository.get_contacts_with_upcoming_birthdays( db=db, user=current_user, )

	return contacts
