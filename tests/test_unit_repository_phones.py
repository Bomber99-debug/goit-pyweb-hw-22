from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from src.entity.models import Phone, User
from src.repository.phones import (
	create_phone,
	delete_phone,
	get_phone_by_id,
	get_phone_by_number,
	get_phones,
	update_phone,
)


class TestPhonesRepository(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()
		self.db.execute = AsyncMock()
		self.db.commit = AsyncMock()
		self.db.refresh = AsyncMock()
		self.db.delete = AsyncMock()

		self.user = User(
			id=1,
			user_name="test_user",
			email="test@example.com",
			password="password",
		)

		self.phone = Phone(
			id=1,
			number="380501234567",
			contact_id=1,
			user=self.user,
		)

	async def test_get_phones(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [self.phone]
		self.db.execute.return_value = mock_result

		result = await get_phones(
			db=self.db,
			user=self.user,
		)

		self.assertEqual(result, [self.phone])
		self.db.execute.assert_awaited_once()

	async def test_get_phone_by_id_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.phone
		self.db.execute.return_value = mock_result

		result = await get_phone_by_id(
			db=self.db,
			user=self.user,
			phone_id=1,
		)

		self.assertEqual(result, self.phone)

	async def test_get_phone_by_id_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None
		self.db.execute.return_value = mock_result

		result = await get_phone_by_id(
			db=self.db,
			user=self.user,
			phone_id=999,
		)

		self.assertIsNone(result)

	async def test_get_phone_by_number_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.phone
		self.db.execute.return_value = mock_result

		result = await get_phone_by_number(
			db=self.db,
			user=self.user,
			phone_number="380501234567",
		)

		self.assertEqual(result, self.phone)

	async def test_get_phone_by_number_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None
		self.db.execute.return_value = mock_result

		result = await get_phone_by_number(
			db=self.db,
			user=self.user,
			phone_number="000000000000",
		)

		self.assertIsNone(result)

	async def test_create_phone(self):
		phone_data = MagicMock()
		phone_data.model_dump.return_value = {
			"number": "380501234567",
			"contact_id": 1,
		}

		result = await create_phone(
			db=self.db,
			user=self.user,
			phone_data=phone_data,
		)

		self.assertIsInstance(result, Phone)
		self.assertEqual(result.number, "380501234567")
		self.assertEqual(result.user, self.user)

		self.db.add.assert_called_once()
		self.db.commit.assert_awaited_once()

	async def test_update_phone_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.phone
		self.db.execute.return_value = mock_result

		phone_data = MagicMock()
		phone_data.number = "380999999999"
		phone_data.contact_id = 2

		result = await update_phone(
			db=self.db,
			user=self.user,
			phone_data=phone_data,
			phone_id=1,
		)

		self.assertEqual(result.number, "380999999999")
		self.assertEqual(result.contact_id, 2)

		self.db.commit.assert_awaited_once()
		self.db.refresh.assert_awaited_once_with(self.phone)

	async def test_update_phone_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None
		self.db.execute.return_value = mock_result

		result = await update_phone(
			db=self.db,
			user=self.user,
			phone_data=MagicMock(),
			phone_id=999,
		)

		self.assertIsNone(result)
		self.db.commit.assert_not_awaited()

	async def test_delete_phone_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.phone
		self.db.execute.return_value = mock_result

		result = await delete_phone(
			db=self.db,
			user=self.user,
			phone_id=1,
		)

		self.assertEqual(result, self.phone)
		self.db.delete.assert_awaited_once_with(self.phone)
		self.db.commit.assert_awaited_once()

	async def test_delete_phone_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None
		self.db.execute.return_value = mock_result

		result = await delete_phone(
			db=self.db,
			user=self.user,
			phone_id=999,
		)

		self.assertIsNone(result)
		self.db.delete.assert_not_awaited()