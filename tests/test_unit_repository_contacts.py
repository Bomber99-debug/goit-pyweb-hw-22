from datetime import date
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock

from src.entity.models import Contact, User
from src.repository.contacts import (
	create_contact,
	delete_contact,
	get_contact_by_id,
	get_contacts,
	update_contact,
)


class TestContactsRepository(IsolatedAsyncioTestCase):

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

		self.contact = Contact(
			id=1,
			first_name="John",
			last_name="Doe",
			email="john@example.com",
			birthday=date(1990, 1, 1),
			notes="Test contact",
			user=self.user,
		)

	async def test_get_contacts(self):
		mock_result = MagicMock()
		mock_result.scalars.return_value.all.return_value = [self.contact]

		self.db.execute.return_value = mock_result

		result = await get_contacts(
			db=self.db,
			user=self.user,
		)

		self.assertEqual(result, [self.contact])
		self.db.execute.assert_awaited_once()

	async def test_get_contact_by_id_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.contact

		self.db.execute.return_value = mock_result

		result = await get_contact_by_id(
			db=self.db,
			user=self.user,
			contact_id=1,
		)

		self.assertEqual(result, self.contact)
		self.db.execute.assert_awaited_once()

	async def test_get_contact_by_id_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		self.db.execute.return_value = mock_result

		result = await get_contact_by_id(
			db=self.db,
			user=self.user,
			contact_id=999,
		)

		self.assertIsNone(result)

	async def test_create_contact(self):
		phone_data = MagicMock()
		phone_data.model_dump.return_value = {
			"number": "380501234567",
			"contact_id": 1,
		}

		contact_data = MagicMock()
		contact_data.model_dump.return_value = {
			"first_name": "John",
			"last_name": "Doe",
			"email": "john@example.com",
			"birthday": date(1990, 1, 1),
			"notes": "Test",
		}
		contact_data.phones = [phone_data]

		result = await create_contact(
			db=self.db,
			user=self.user,
			contact_data=contact_data,
		)

		self.assertIsInstance(result, Contact)
		self.assertEqual(result.first_name, "John")
		self.assertEqual(result.user, self.user)

		self.db.add.assert_called_once()
		self.db.commit.assert_awaited_once()

	async def test_update_contact_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.contact

		self.db.execute.return_value = mock_result

		contact_data = MagicMock()
		contact_data.first_name = "Jane"
		contact_data.last_name = "Doe"
		contact_data.email = "jane@example.com"
		contact_data.birthday = date(1991, 2, 2)
		contact_data.notes = "Updated"

		result = await update_contact(
			db=self.db,
			user=self.user,
			contact_data=contact_data,
			contact_id=1,
		)

		self.assertEqual(result.first_name, "Jane")
		self.assertEqual(result.email, "jane@example.com")

		self.db.commit.assert_awaited_once()
		self.db.refresh.assert_awaited_once_with(self.contact)

	async def test_update_contact_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		self.db.execute.return_value = mock_result

		result = await update_contact(
			db=self.db,
			user=self.user,
			contact_data=MagicMock(),
			contact_id=999,
		)

		self.assertIsNone(result)
		self.db.commit.assert_not_awaited()

	async def test_delete_contact_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = self.contact

		self.db.execute.return_value = mock_result

		result = await delete_contact(
			db=self.db,
			user=self.user,
			contact_id=1,
		)

		self.assertEqual(result, self.contact)

		self.db.delete.assert_awaited_once_with(self.contact)
		self.db.commit.assert_awaited_once()

	async def test_delete_contact_not_found(self):
		mock_result = MagicMock()
		mock_result.scalar_one_or_none.return_value = None

		self.db.execute.return_value = mock_result

		result = await delete_contact(
			db=self.db,
			user=self.user,
			contact_id=999,
		)

		self.assertIsNone(result)
		self.db.delete.assert_not_awaited()
		self.db.commit.assert_not_awaited()