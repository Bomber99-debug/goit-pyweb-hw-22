import pickle
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from src.routes.contacts import (
	create_contact,
	delete_contact,
	get_contact_by_id,
	get_contacts,
	update_contact,
)


class TestContactRoutes(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()

		self.user = SimpleNamespace(
			id=1,
			email="owner@example.com",
			user_name="owner",
		)

		self.contact = SimpleNamespace(
			id=10,
			first_name="John",
			last_name="Doe",
			email="john@example.com",
		)

		self.contacts = [
			self.contact,
		]

	def make_async_iterator(
		self,
		items,
	):
		async def iterator():
			for item in items:
				yield item

		return iterator()

	# ---------------------------------------------------------------
	# get_contacts
	# ---------------------------------------------------------------

	async def test_get_contacts_cache_miss(self):
		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contacts",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)
			mock_redis.set = AsyncMock()
			mock_redis.expire = AsyncMock()

			mock_repository.return_value = self.contacts

			result = await get_contacts(
				limit=10,
				offset=0,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.contacts,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				skip=0,
				limit=10,
				user=self.user,
			)

			cache_key = (
				"current_user:1:"
				"contacts:"
				"limit:10:"
				"offset:0"
			)

			mock_redis.get.assert_awaited_once_with(
				cache_key,
			)

			mock_redis.set.assert_awaited_once()

			mock_redis.expire.assert_awaited_once_with(
				name=cache_key,
				time=60,
			)

	async def test_get_contacts_cache_hit(self):
		cached_contacts = pickle.dumps(
			self.contacts,
		)

		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contacts",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=cached_contacts,
			)

			result = await get_contacts(
				limit=10,
				offset=0,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result[0].id,
				self.contact.id,
			)

			mock_repository.assert_not_awaited()

	async def test_get_contacts_not_found(self):
		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contacts",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)

			mock_repository.return_value = None

			with self.assertRaises(
				HTTPException,
			) as error:
				await get_contacts(
					limit=10,
					offset=0,
					db=self.db,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				404,
			)

			self.assertEqual(
				error.exception.detail,
				"Contact not found",
			)

	# ---------------------------------------------------------------
	# get_contact_by_id
	# ---------------------------------------------------------------

	async def test_get_contact_by_id_cache_miss(self):
		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contact_by_id",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)
			mock_redis.set = AsyncMock()
			mock_redis.expire = AsyncMock()

			mock_repository.return_value = self.contact

			result = await get_contact_by_id(
				db=self.db,
				contact_id=10,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.contact,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				contact_id=10,
				user=self.user,
			)

			cache_key = (
				"current_user:1:"
				"contact_id:10"
			)

			mock_redis.get.assert_awaited_once_with(
				cache_key,
			)

			mock_redis.set.assert_awaited_once()

			mock_redis.expire.assert_awaited_once_with(
				cache_key,
				time=60,
			)

	async def test_get_contact_by_id_cache_hit(self):
		cached_contact = pickle.dumps(
			self.contact,
		)

		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contact_by_id",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=cached_contact,
			)

			result = await get_contact_by_id(
				db=self.db,
				contact_id=10,
				current_user=self.user,
			)

			self.assertEqual(
				result.id,
				10,
			)

			mock_repository.assert_not_awaited()

	async def test_get_contact_by_id_not_found(self):
		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.get_contact_by_id",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)

			mock_repository.return_value = None

			with self.assertRaises(
				HTTPException,
			) as error:
				await get_contact_by_id(
					db=self.db,
					contact_id=999,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				404,
			)

			self.assertEqual(
				error.exception.detail,
				"Contact not found",
			)

	# ---------------------------------------------------------------
	# create_contact
	# ---------------------------------------------------------------

	async def test_create_contact_success(self):
		phone = SimpleNamespace(
			number="+380991112233",
		)

		contact_data = SimpleNamespace(
			first_name="John",
			last_name="Doe",
			email="john@example.com",
			phones=[
				phone,
			],
		)

		background_tasks = MagicMock()
		request = MagicMock()

		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.phones_repository.get_phone_by_number",
				new_callable=AsyncMock,
			) as mock_get_phone,
			patch(
				"src.routes.contacts.contact_repository.create_contact",
				new_callable=AsyncMock,
			) as mock_create_contact,
		):
			mock_get_phone.return_value = None
			mock_create_contact.return_value = self.contact

			mock_redis.scan_iter = MagicMock(
				return_value=self.make_async_iterator(
					[
						b"contacts-cache-1",
						b"contacts-cache-2",
					],
				),
			)

			mock_redis.delete = AsyncMock()

			result = await create_contact(
				contact_data=contact_data,
				bt=background_tasks,
				request=request,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.contact,
			)

			mock_get_phone.assert_awaited_once_with(
				db=self.db,
				phone_number="+380991112233",
				user=self.user,
			)

			mock_create_contact.assert_awaited_once_with(
				db=self.db,
				contact_data=contact_data,
				user=self.user,
			)

			mock_redis.scan_iter.assert_called_once_with(
				match="current_user:1:contacts:*",
			)

			self.assertEqual(
				mock_redis.delete.await_count,
				2,
			)

			background_tasks.add_task.assert_called_once()

	async def test_create_contact_duplicate_phone(self):
		phone_data = SimpleNamespace(
			number="+380991112233",
		)

		contact_data = SimpleNamespace(
			first_name="John",
			last_name="Doe",
			email="john@example.com",
			phones=[
				phone_data,
			],
		)

		existing_phone = SimpleNamespace(
			id=5,
			number="+380991112233",
		)

		with patch(
			"src.routes.contacts.phones_repository.get_phone_by_number",
			new_callable=AsyncMock,
		) as mock_get_phone:
			mock_get_phone.return_value = existing_phone

			with self.assertRaises(
				HTTPException,
			) as error:
				await create_contact(
					contact_data=contact_data,
					bt=MagicMock(),
					request=MagicMock(),
					db=self.db,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				409,
			)

			self.assertEqual(
				error.exception.detail,
				"Phone already exists",
			)

	# ---------------------------------------------------------------
	# update_contact
	# ---------------------------------------------------------------

	async def test_update_contact_success(self):
		contact_data = SimpleNamespace(
			first_name="Updated",
			last_name="Contact",
			email="updated@example.com",
		)

		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.update_contact",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_repository.return_value = self.contact

			mock_redis.delete = AsyncMock()

			mock_redis.scan_iter = MagicMock(
				side_effect=lambda match: self.make_async_iterator(
					[
						f"{match}:key".encode(),
					],
				),
			)

			result = await update_contact(
				contact_data=contact_data,
				contact_id=10,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.contact,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				contact_data=contact_data,
				contact_id=10,
				user=self.user,
			)

			mock_redis.delete.assert_any_await(
				"current_user:1:contact_id:10",
			)

			self.assertEqual(
				mock_redis.scan_iter.call_count,
				2,
			)

	async def test_update_contact_not_found(self):
		contact_data = SimpleNamespace()

		with patch(
			"src.routes.contacts.contact_repository.update_contact",
			new_callable=AsyncMock,
		) as mock_repository:
			mock_repository.return_value = None

			with self.assertRaises(
				HTTPException,
			) as error:
				await update_contact(
					contact_data=contact_data,
					contact_id=999,
					db=self.db,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				404,
			)

			self.assertEqual(
				error.exception.detail,
				"Contact not found",
			)

	# ---------------------------------------------------------------
	# delete_contact
	# ---------------------------------------------------------------

	async def test_delete_contact(self):
		with (
			patch(
				"src.routes.contacts.redis_client",
			) as mock_redis,
			patch(
				"src.routes.contacts.contact_repository.delete_contact",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_repository.return_value = self.contact

			mock_redis.delete = AsyncMock()

			mock_redis.scan_iter = MagicMock(
				side_effect=lambda match: self.make_async_iterator(
					[
						f"{match}:key".encode(),
					],
				),
			)

			result = await delete_contact(
				db=self.db,
				contact_id=10,
				current_user=self.user,
			)

			self.assertIsNone(
				result,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				contact_id=10,
				user=self.user,
			)

			mock_redis.delete.assert_any_await(
				"current_user:1:contact_id:10",
			)

			self.assertEqual(
				mock_redis.scan_iter.call_count,
				2,
			)