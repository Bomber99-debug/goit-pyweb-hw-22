from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from src.entity.models import User
from src.repository.email import (
	confirmed_email,
	get_user_by_email,
)


class TestEmailRepository(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()
		self.db.execute = AsyncMock()
		self.db.commit = AsyncMock()

		self.user = User(
			id=1,
			user_name="test_user",
			email="test@example.com",
			password="hashed_password",
			confirmed=False,
		)

	async def test_get_user_by_email(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.user
		self.db.execute.return_value = mock_result

		result = await get_user_by_email(
			email="test@example.com",
			db=self.db,
		)

		self.assertEqual(result, self.user)

	@patch(
		"src.repository.email.get_user_by_email",
		new_callable=AsyncMock,
	)
	async def test_confirmed_email(self, mock_get_user):
		mock_get_user.return_value = self.user

		await confirmed_email(
			email="test@example.com",
			db=self.db,
		)

		self.assertTrue(self.user.confirmed)
		self.db.commit.assert_awaited_once()