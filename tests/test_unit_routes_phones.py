import pickle
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from src.routes.phones import (
	create_phone,
	delete_phone,
	get_phone_by_id,
	get_phones,
	update_phone,
)


class TestPhoneRoutes(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()

		self.user = SimpleNamespace(
			id=1,
			email="owner@example.com",
			user_name="owner",
		)

		self.phone = SimpleNamespace(
			id=10,
			number="+380991112233",
			contact_id=5,
		)

		self.phones = [
			self.phone,
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
	# get_phones
	# ---------------------------------------------------------------

	async def test_get_phones_cache_miss(self):
		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phones",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)
			mock_redis.set = AsyncMock()
			mock_redis.expire = AsyncMock()

			mock_repository.return_value = self.phones

			result = await get_phones(
				limit=10,
				offset=0,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.phones,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				skip=0,
				limit=10,
				user=self.user,
			)

			cache_key = (
				"current_user:1:"
				"phones:"
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

	async def test_get_phones_cache_hit(self):
		cached_phones = pickle.dumps(
			self.phones,
		)

		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phones",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=cached_phones,
			)

			result = await get_phones(
				limit=10,
				offset=0,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result[0].id,
				self.phone.id,
			)

			self.assertEqual(
				result[0].number,
				self.phone.number,
			)

			mock_repository.assert_not_awaited()

	async def test_get_phones_not_found(self):
		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phones",
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
				await get_phones(
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
				"Phone not found",
			)

	# ---------------------------------------------------------------
	# get_phone_by_id
	# ---------------------------------------------------------------

	async def test_get_phone_by_id_cache_miss(self):
		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phone_by_id",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)
			mock_redis.set = AsyncMock()
			mock_redis.expire = AsyncMock()

			mock_repository.return_value = self.phone

			result = await get_phone_by_id(
				db=self.db,
				phone_id=10,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.phone,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				phone_id=10,
				user=self.user,
			)

			cache_key = (
				"current_user:1:"
				"phone_id:10"
			)

			mock_redis.get.assert_awaited_once_with(
				cache_key,
			)

			mock_redis.set.assert_awaited_once()

			mock_redis.expire.assert_awaited_once_with(
				cache_key,
				time=60,
			)

	async def test_get_phone_by_id_cache_hit(self):
		cached_phone = pickle.dumps(
			self.phone,
		)

		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phone_by_id",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_redis.get = AsyncMock(
				return_value=cached_phone,
			)

			result = await get_phone_by_id(
				db=self.db,
				phone_id=10,
				current_user=self.user,
			)

			self.assertEqual(
				result.id,
				10,
			)

			self.assertEqual(
				result.number,
				"+380991112233",
			)

			mock_repository.assert_not_awaited()

	async def test_get_phone_by_id_not_found(self):
		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phone_by_id",
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
				await get_phone_by_id(
					db=self.db,
					phone_id=999,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				404,
			)

			self.assertEqual(
				error.exception.detail,
				"Phone not found",
			)

	# ---------------------------------------------------------------
	# create_phone
	# ---------------------------------------------------------------

	async def test_create_phone_success(self):
		phone_data = SimpleNamespace(
			number="+380991112233",
			contact_id=5,
		)

		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phone_by_number",
				new_callable=AsyncMock,
			) as mock_get_phone,
			patch(
				"src.routes.phones.phones_repository.create_phone",
				new_callable=AsyncMock,
			) as mock_create_phone,
		):
			mock_get_phone.return_value = None
			mock_create_phone.return_value = self.phone

			mock_redis.delete = AsyncMock()

			mock_redis.scan_iter = MagicMock(
				side_effect=lambda match: self.make_async_iterator(
					[
						f"{match}:key".encode(),
					],
				),
			)

			result = await create_phone(
				phone_data=phone_data,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				self.phone,
			)

			mock_get_phone.assert_awaited_once_with(
				db=self.db,
				phone_number="+380991112233",
				user=self.user,
			)

			mock_create_phone.assert_awaited_once_with(
				db=self.db,
				phone_data=phone_data,
				user=self.user,
			)

			self.assertEqual(
				mock_redis.scan_iter.call_count,
				2,
			)

			mock_redis.scan_iter.assert_any_call(
				match="current_user:1:phones:*",
			)

			mock_redis.scan_iter.assert_any_call(
				match="current_user:1:contacts:*",
			)

			self.assertEqual(
				mock_redis.delete.await_count,
				2,
			)

	async def test_create_phone_duplicate(self):
		phone_data = SimpleNamespace(
			number="+380991112233",
			contact_id=5,
		)

		existing_phone = SimpleNamespace(
			id=20,
			number="+380991112233",
		)

		with patch(
			"src.routes.phones.phones_repository.get_phone_by_number",
			new_callable=AsyncMock,
		) as mock_get_phone:
			mock_get_phone.return_value = existing_phone

			with self.assertRaises(
				HTTPException,
			) as error:
				await create_phone(
					phone_data=phone_data,
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
	# update_phone
	# ---------------------------------------------------------------

	async def test_update_phone_success(self):
		phone_data = SimpleNamespace(
			number="+380992223344",
			contact_id=5,
		)

		updated_phone = SimpleNamespace(
			id=10,
			number="+380992223344",
			contact_id=5,
		)

		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.get_phone_by_number",
				new_callable=AsyncMock,
			) as mock_get_phone,
			patch(
				"src.routes.phones.phones_repository.update_phone",
				new_callable=AsyncMock,
			) as mock_update_phone,
		):
			mock_get_phone.return_value = None
			mock_update_phone.return_value = updated_phone

			mock_redis.delete = AsyncMock()

			mock_redis.scan_iter = MagicMock(
				side_effect=lambda match: self.make_async_iterator(
					[
						f"{match}:key".encode(),
					],
				),
			)

			result = await update_phone(
				phone_data=phone_data,
				phone_id=10,
				db=self.db,
				current_user=self.user,
			)

			self.assertEqual(
				result,
				updated_phone,
			)

			mock_get_phone.assert_awaited_once_with(
				db=self.db,
				phone_number="+380992223344",
				user=self.user,
			)

			mock_update_phone.assert_awaited_once_with(
				db=self.db,
				phone_data=phone_data,
				phone_id=10,
				user=self.user,
			)

			mock_redis.delete.assert_any_await(
				"current_user:1:phone_id:10",
			)

			self.assertEqual(
				mock_redis.scan_iter.call_count,
				2,
			)

	async def test_update_phone_duplicate(self):
		phone_data = SimpleNamespace(
			number="+380991112233",
			contact_id=5,
		)

		existing_phone = SimpleNamespace(
			id=20,
			number="+380991112233",
		)

		with patch(
			"src.routes.phones.phones_repository.get_phone_by_number",
			new_callable=AsyncMock,
		) as mock_get_phone:
			mock_get_phone.return_value = existing_phone

			with self.assertRaises(
				HTTPException,
			) as error:
				await update_phone(
					phone_data=phone_data,
					phone_id=10,
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

	async def test_update_phone_not_found(self):
		phone_data = SimpleNamespace(
			number="+380992223344",
			contact_id=5,
		)

		with (
			patch(
				"src.routes.phones.phones_repository.get_phone_by_number",
				new_callable=AsyncMock,
			) as mock_get_phone,
			patch(
				"src.routes.phones.phones_repository.update_phone",
				new_callable=AsyncMock,
			) as mock_update_phone,
		):
			mock_get_phone.return_value = None
			mock_update_phone.return_value = None

			with self.assertRaises(
				HTTPException,
			) as error:
				await update_phone(
					phone_data=phone_data,
					phone_id=999,
					db=self.db,
					current_user=self.user,
				)

			self.assertEqual(
				error.exception.status_code,
				404,
			)

			self.assertEqual(
				error.exception.detail,
				"Phone not found",
			)

	# ---------------------------------------------------------------
	# delete_phone
	# ---------------------------------------------------------------

	async def test_delete_phone(self):
		with (
			patch(
				"src.routes.phones.redis_client",
			) as mock_redis,
			patch(
				"src.routes.phones.phones_repository.delete_phone",
				new_callable=AsyncMock,
			) as mock_repository,
		):
			mock_repository.return_value = self.phone

			mock_redis.delete = AsyncMock()

			mock_redis.scan_iter = MagicMock(
				side_effect=lambda match: self.make_async_iterator(
					[
						f"{match}:key".encode(),
					],
				),
			)

			result = await delete_phone(
				db=self.db,
				phone_id=10,
				current_user=self.user,
			)

			self.assertIsNone(
				result,
			)

			mock_repository.assert_awaited_once_with(
				db=self.db,
				phone_id=10,
				user=self.user,
			)

			mock_redis.delete.assert_any_await(
				"current_user:1:phone_id:10",
			)

			self.assertEqual(
				mock_redis.scan_iter.call_count,
				2,
			)