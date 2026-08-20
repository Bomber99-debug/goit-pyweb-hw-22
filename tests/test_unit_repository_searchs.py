from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from src.entity.models import Contact, User
from src.repository.searchs import (
	get_contacts_with_upcoming_birthdays,
	search_contacts,
)


class TestSearchRepository(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()
		self.db.execute = AsyncMock()

		self.user = User(
			id=1,
			user_name="test_user",
			email="test@example.com",
			password="password",
		)

		self.contact = MagicMock(spec=Contact)

	async def test_search_contacts(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [
			self.contact,
		]

		self.db.execute.return_value = mock_result

		result = await search_contacts(
			db=self.db,
			user=self.user,
			query="John",
		)

		self.assertEqual(result, [self.contact])
		self.db.execute.assert_awaited_once()

	async def test_search_contacts_empty_result(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = []
		self.db.execute.return_value = mock_result

		result = await search_contacts(
			db=self.db,
			user=self.user,
			query="missing",
		)

		self.assertEqual(result, [])

	async def test_get_contacts_with_upcoming_birthdays(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [
			self.contact,
		]

		self.db.execute.return_value = mock_result

		result = await get_contacts_with_upcoming_birthdays(
			db=self.db,
			user=self.user,
		)

		self.assertEqual(result, [self.contact])
		self.db.execute.assert_awaited_once()

	async def test_get_contacts_with_upcoming_birthdays_empty(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = []
		self.db.execute.return_value = mock_result

		result = await get_contacts_with_upcoming_birthdays(
			db=self.db,
			user=self.user,
		)

		self.assertEqual(result, [])