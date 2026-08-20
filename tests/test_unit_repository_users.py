from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from src.entity.models import User
from src.repository.users import (
	create_user,
	get_user_by_email,
	update_avatar,
	update_token,
)


class TestUsersRepository(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()
		self.db.execute = AsyncMock()
		self.db.commit = AsyncMock()
		self.db.refresh = AsyncMock()

		self.user = User(
			id=1,
			user_name="test_user",
			email="test@example.com",
			password="hashed_password",
			avatar=None,
		)

	async def test_get_user_by_email_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.user
		self.db.execute.return_value = mock_result

		result = await get_user_by_email(
			email="test@example.com",
			db=self.db,
		)

		self.assertEqual(result, self.user)
		self.db.execute.assert_awaited_once()

	async def test_get_user_by_email_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None
		self.db.execute.return_value = mock_result

		result = await get_user_by_email(
			email="missing@example.com",
			db=self.db,
		)

		self.assertIsNone(result)

	@patch("src.repository.users.Gravatar")
	async def test_create_user_without_avatar(self, mock_gravatar):
		mock_gravatar.return_value.get_image.return_value = (
			"https://example.com/avatar.png"
		)

		body = MagicMock()
		body.avatar = None
		body.email = "test@example.com"

		body.model_dump.return_value = {
			"user_name": "test_user",
			"email": "test@example.com",
			"password": "hashed_password",
			"avatar": "https://example.com/avatar.png",
		}

		result = await create_user(
			body=body,
			db=self.db,
		)

		self.assertIsInstance(result, User)

		self.db.add.assert_called_once()
		self.db.commit.assert_awaited_once()
		self.db.refresh.assert_awaited_once()

	async def test_create_user_with_avatar(self):
		body = MagicMock()
		body.avatar = "https://example.com/my-avatar.png"
		body.email = "test@example.com"

		body.model_dump.return_value = {
			"user_name": "test_user",
			"email": "test@example.com",
			"password": "hashed_password",
			"avatar": "https://example.com/my-avatar.png",
		}

		result = await create_user(
			body=body,
			db=self.db,
		)

		self.assertEqual(
			result.avatar,
			"https://example.com/my-avatar.png",
		)

		self.db.commit.assert_awaited_once()

	async def test_update_token(self):
		await update_token(
			user=self.user,
			token="refresh-token",
			db=self.db,
		)

		self.assertEqual(
			self.user.refresh_token,
			"refresh-token",
		)

		self.db.commit.assert_awaited_once()

	@patch(
		"src.repository.users.get_user_by_email",
		new_callable=AsyncMock,
	)
	async def test_update_avatar(self, mock_get_user):
		mock_get_user.return_value = self.user

		result = await update_avatar(
			email="test@example.com",
			url="https://example.com/new-avatar.png",
			db=self.db,
		)

		self.assertEqual(
			result.avatar,
			"https://example.com/new-avatar.png",
		)

		self.db.commit.assert_awaited_once()