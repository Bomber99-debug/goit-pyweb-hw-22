import pickle
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from jose import jwt

from src.services.auth import Auth


class TestAuthService(IsolatedAsyncioTestCase):

	def setUp(self):
		self.auth = Auth()

		# We do not depend on the real .env secret in unit tests.
		self.auth.SECRET_KEY = "test-secret-key"
		self.auth.ALGORITHM = "HS256"

		self.db = MagicMock()

		self.user = SimpleNamespace(
			id=1,
			email="test@example.com",
			user_name="test_user",
		)

	def test_password_hash_and_verify(self):
		password = "secret123"

		hashed_password = self.auth.get_password_hash(
			password,
		)

		self.assertNotEqual(
			hashed_password,
			password,
		)

		self.assertTrue(
			self.auth.verify_password(
				password,
				hashed_password,
			),
		)

		self.assertFalse(
			self.auth.verify_password(
				"wrong-password",
				hashed_password,
			),
		)

	async def test_create_access_token_default_expiration(self):
		token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
		)

		payload = jwt.decode(
			token,
			self.auth.SECRET_KEY,
			algorithms=[
				self.auth.ALGORITHM,
			],
		)

		self.assertEqual(
			payload["sub"],
			self.user.email,
		)

		self.assertEqual(
			payload["scope"],
			"access_token",
		)

		self.assertIn(
			"iat",
			payload,
		)

		self.assertIn(
			"exp",
			payload,
		)

	async def test_create_access_token_custom_expiration(self):
		token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
			expires_delta=60,
		)

		payload = jwt.decode(
			token,
			self.auth.SECRET_KEY,
			algorithms=[
				self.auth.ALGORITHM,
			],
		)

		self.assertEqual(
			payload["scope"],
			"access_token",
		)

		self.assertAlmostEqual(
			payload["exp"] - payload["iat"],
			60,
			delta=1,
		)

	async def test_create_refresh_token_default_expiration(self):
		token = await self.auth.create_refresh_token(
			data={
				"sub": self.user.email,
			},
		)

		payload = jwt.decode(
			token,
			self.auth.SECRET_KEY,
			algorithms=[
				self.auth.ALGORITHM,
			],
		)

		self.assertEqual(
			payload["sub"],
			self.user.email,
		)

		self.assertEqual(
			payload["scope"],
			"refresh_token",
		)

	async def test_create_refresh_token_custom_expiration(self):
		token = await self.auth.create_refresh_token(
			data={
				"sub": self.user.email,
			},
			expires_delta=120,
		)

		payload = jwt.decode(
			token,
			self.auth.SECRET_KEY,
			algorithms=[
				self.auth.ALGORITHM,
			],
		)

		self.assertAlmostEqual(
			payload["exp"] - payload["iat"],
			120,
			delta=1,
		)

	async def test_decode_refresh_token_success(self):
		token = await self.auth.create_refresh_token(
			data={
				"sub": self.user.email,
			},
		)

		email = await self.auth.decode_refresh_token(
			token,
		)

		self.assertEqual(
			email,
			self.user.email,
		)

	async def test_decode_refresh_token_invalid_scope(self):
		access_token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
		)

		with self.assertRaises(HTTPException) as error:
			await self.auth.decode_refresh_token(
				access_token,
			)

		self.assertEqual(
			error.exception.status_code,
			401,
		)

		self.assertEqual(
			error.exception.detail,
			"Invalid scope for token",
		)

	async def test_decode_refresh_token_invalid_token(self):
		with self.assertRaises(HTTPException) as error:
			await self.auth.decode_refresh_token(
				"invalid-token",
			)

		self.assertEqual(
			error.exception.status_code,
			401,
		)

		self.assertEqual(
			error.exception.detail,
			"Could not validate credentials",
		)

	async def test_get_current_user_from_database(self):
		token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
		)

		with (
			patch(
				"src.services.auth.redis_client",
			) as mock_redis,
			patch(
				"src.services.auth.users_repository.get_user_by_email",
				new_callable=AsyncMock,
			) as mock_get_user,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)
			mock_redis.set = AsyncMock()
			mock_redis.expire = AsyncMock()

			mock_get_user.return_value = self.user

			result = await self.auth.get_current_user(
				token=token,
				db=self.db,
			)

			self.assertEqual(
				result,
				self.user,
			)

			mock_get_user.assert_awaited_once_with(
				email=self.user.email,
				db=self.db,
			)

			mock_redis.get.assert_awaited_once_with(
				f"access_token:{self.user.email}",
			)

			mock_redis.set.assert_awaited_once()

			mock_redis.expire.assert_awaited_once_with(
				name=f"access_token:{self.user.email}",
				time=900,
			)

	async def test_get_current_user_from_cache(self):
		token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
		)

		cached_user = pickle.dumps(
			self.user,
		)

		with (
			patch(
				"src.services.auth.redis_client",
			) as mock_redis,
			patch(
				"src.services.auth.users_repository.get_user_by_email",
				new_callable=AsyncMock,
			) as mock_get_user,
		):
			mock_redis.get = AsyncMock(
				return_value=cached_user,
			)

			result = await self.auth.get_current_user(
				token=token,
				db=self.db,
			)

			self.assertEqual(
				result.email,
				self.user.email,
			)

			self.assertEqual(
				result.id,
				self.user.id,
			)

			mock_get_user.assert_not_awaited()

	async def test_get_current_user_not_found(self):
		token = await self.auth.create_access_token(
			data={
				"sub": self.user.email,
			},
		)

		with (
			patch(
				"src.services.auth.redis_client",
			) as mock_redis,
			patch(
				"src.services.auth.users_repository.get_user_by_email",
				new_callable=AsyncMock,
			) as mock_get_user,
		):
			mock_redis.get = AsyncMock(
				return_value=None,
			)

			mock_get_user.return_value = None

			with self.assertRaises(HTTPException) as error:
				await self.auth.get_current_user(
					token=token,
					db=self.db,
				)

			self.assertEqual(
				error.exception.status_code,
				401,
			)

			self.assertEqual(
				error.exception.detail,
				"Could not validate credentials",
			)

	async def test_get_current_user_with_refresh_token(self):
		token = await self.auth.create_refresh_token(
			data={
				"sub": self.user.email,
			},
		)

		with self.assertRaises(HTTPException) as error:
			await self.auth.get_current_user(
				token=token,
				db=self.db,
			)

		self.assertEqual(
			error.exception.status_code,
			401,
		)

	async def test_get_current_user_invalid_token(self):
		with self.assertRaises(HTTPException) as error:
			await self.auth.get_current_user(
				token="invalid-token",
				db=self.db,
			)

		self.assertEqual(
			error.exception.status_code,
			401,
		)

		self.assertEqual(
			error.exception.detail,
			"Could not validate credentials",
		)

	async def test_get_current_user_without_email(self):
		with patch(
			"src.services.auth.jwt.decode",
			return_value={
				"scope": "access_token",
				"sub": None,
			},
		):
			with self.assertRaises(HTTPException) as error:
				await self.auth.get_current_user(
					token="test-token",
					db=self.db,
				)

		self.assertEqual(
			error.exception.status_code,
			401,
		)

	def test_create_email_token(self):
		token = self.auth.create_email_token(
			{
				"sub": self.user.email,
			},
		)

		payload = jwt.decode(
			token,
			self.auth.SECRET_KEY,
			algorithms=[
				self.auth.ALGORITHM,
			],
		)

		self.assertEqual(
			payload["sub"],
			self.user.email,
		)

		self.assertIn(
			"iat",
			payload,
		)

		self.assertIn(
			"exp",
			payload,
		)

	async def test_get_email_from_token_success(self):
		token = self.auth.create_email_token(
			{
				"sub": self.user.email,
			},
		)

		email = await self.auth.get_email_from_token(
			token,
		)

		self.assertEqual(
			email,
			self.user.email,
		)

	async def test_get_email_from_token_invalid(self):
		with self.assertRaises(HTTPException) as error:
			await self.auth.get_email_from_token(
				"invalid-token",
			)

		self.assertEqual(
			error.exception.status_code,
			422,
		)

		self.assertEqual(
			error.exception.detail,
			"Invalid token for email verification",
		)