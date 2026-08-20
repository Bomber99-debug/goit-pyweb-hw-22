from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from src.routes.searchs import (get_contacts_with_upcoming_birthdays, search_contacts,
                                )


def unwrap_handler( handler ):
	while hasattr( handler, "__wrapped__" ):
		handler = handler.__wrapped__

	return handler


class TestSearchRoutes( IsolatedAsyncioTestCase ):

	def setUp( self ):
		self.db = MagicMock()

		self.user = SimpleNamespace( id=1, email="test@example.com", )

		self.contacts = [ SimpleNamespace( id=1, first_name="John", ), SimpleNamespace( id=2, first_name="Jane", ),
				]

	@patch( "src.routes.searchs.search_repository.search_contacts", new_callable=AsyncMock, )
	async def test_search_contacts( self, mock_search_contacts, ):
		mock_search_contacts.return_value = self.contacts

		handler = unwrap_handler( search_contacts, )

		result = await handler( query="John", db=self.db, current_user=self.user, )

		self.assertEqual( result, self.contacts, )

		mock_search_contacts.assert_awaited_once_with( db=self.db, query="John", user=self.user, )

	@patch( "src.routes.searchs.search_repository.get_contacts_with_upcoming_birthdays", new_callable=AsyncMock, )
	async def test_get_contacts_with_upcoming_birthdays( self, mock_get_birthdays, ):
		mock_get_birthdays.return_value = self.contacts

		handler = unwrap_handler( get_contacts_with_upcoming_birthdays, )

		result = await handler( db=self.db, current_user=self.user, )

		self.assertEqual( result, self.contacts, )

		mock_get_birthdays.assert_awaited_once_with( db=self.db, user=self.user, )
