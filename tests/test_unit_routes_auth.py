from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from src.routes.auth import (login, refresh_token, signup, update_avatar_user,
                             )


class TestAuthRoutes( IsolatedAsyncioTestCase ):

	def setUp( self ):
		self.db = MagicMock()

		self.user = SimpleNamespace( id=1,
				user_name="test_user",
				email="test@example.com",
				password="hashed_password",
				confirmed=True,
				refresh_token="old-refresh-token",
				avatar=None, )

	# ------------------------------------------------------------------
	# signup
	# ------------------------------------------------------------------

	@patch( "src.routes.auth.users_repository.create_user", new_callable=AsyncMock, )
	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.get_password_hash", )
	async def test_signup_success( self, mock_get_password_hash, mock_get_user, mock_create_user, ):
		body = SimpleNamespace( email="test@example.com", user_name="test_user", password="plain-password", )

		background_tasks = MagicMock()

		request = SimpleNamespace( base_url="http://testserver/", )

		mock_get_user.return_value = None

		mock_get_password_hash.return_value = "hashed-password"

		mock_create_user.return_value = self.user

		result = await signup( body=body, bt=background_tasks, request=request, db=self.db, )

		self.assertEqual( result, self.user, )

		self.assertEqual( body.password, "hashed-password", )

		mock_get_user.assert_awaited_once_with( email="test@example.com", db=self.db, )

		mock_get_password_hash.assert_called_once_with( "plain-password", )

		mock_create_user.assert_awaited_once_with( body=body, db=self.db, )

		background_tasks.add_task.assert_called_once()

	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	async def test_signup_existing_user( self, mock_get_user, ):
		body = SimpleNamespace( email="test@example.com", user_name="test_user", password="plain-password", )

		background_tasks = MagicMock()

		request = SimpleNamespace( base_url="http://testserver/", )

		mock_get_user.return_value = self.user

		with self.assertRaises( HTTPException ) as error:
			await signup( body=body, bt=background_tasks, request=request, db=self.db, )

		self.assertEqual( error.exception.status_code, 409, )

		self.assertEqual( error.exception.detail, "Account already exists", )

		background_tasks.add_task.assert_not_called()

	# ------------------------------------------------------------------
	# login
	# ------------------------------------------------------------------

	@patch( "src.routes.auth.users_repository.update_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.create_refresh_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.create_access_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.verify_password", )
	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	async def test_login_success( self,
			mock_get_user,
			mock_verify_password,
			mock_create_access_token,
			mock_create_refresh_token,
			mock_update_token, ):
		body = SimpleNamespace( username="test@example.com", password="plain-password", )

		mock_get_user.return_value = self.user
		mock_verify_password.return_value = True

		mock_create_access_token.return_value = "access-token"
		mock_create_refresh_token.return_value = "refresh-token"

		result = await login( body=body, db=self.db, )

		self.assertEqual( result,
				{ "access_token": "access-token", "refresh_token": "refresh-token", "token_type": "bearer",
						}, )

		mock_get_user.assert_awaited_once_with( email="test@example.com", db=self.db, )

		mock_verify_password.assert_called_once_with( "plain-password", "hashed_password", )

		mock_create_access_token.assert_awaited_once_with( data={ "sub": "test@example.com",
				}, )

		mock_create_refresh_token.assert_awaited_once_with( data={ "sub": "test@example.com",
				}, )

		mock_update_token.assert_awaited_once_with( user=self.user, token="refresh-token", db=self.db, )

	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	async def test_login_invalid_email( self, mock_get_user, ):
		body = SimpleNamespace( username="missing@example.com", password="password", )

		mock_get_user.return_value = None

		with self.assertRaises( HTTPException ) as error:
			await login( body=body, db=self.db, )

		self.assertEqual( error.exception.status_code, 401, )

		self.assertEqual( error.exception.detail, "Invalid email", )

	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	async def test_login_email_not_confirmed( self, mock_get_user, ):
		user = SimpleNamespace( email="test@example.com", password="hashed_password", confirmed=False, )

		body = SimpleNamespace( username="test@example.com", password="password", )

		mock_get_user.return_value = user

		with self.assertRaises( HTTPException ) as error:
			await login( body=body, db=self.db, )

		self.assertEqual( error.exception.status_code, 401, )

		self.assertEqual( error.exception.detail, "Email not confirmed", )

	@patch( "src.routes.auth.auth_service.verify_password", )
	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	async def test_login_invalid_password( self, mock_get_user, mock_verify_password, ):
		body = SimpleNamespace( username="test@example.com", password="wrong-password", )

		mock_get_user.return_value = self.user
		mock_verify_password.return_value = False

		with self.assertRaises( HTTPException ) as error:
			await login( body=body, db=self.db, )

		self.assertEqual( error.exception.status_code, 401, )

		self.assertEqual( error.exception.detail, "Invalid password", )

	# ------------------------------------------------------------------
	# refresh_token
	# ------------------------------------------------------------------

	@patch( "src.routes.auth.users_repository.update_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.create_refresh_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.create_access_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.decode_refresh_token", new_callable=AsyncMock, )
	async def test_refresh_token_success( self,
			mock_decode_refresh_token,
			mock_get_user,
			mock_create_access_token,
			mock_create_refresh_token,
			mock_update_token, ):
		credentials = SimpleNamespace( credentials="old-refresh-token", )

		self.user.refresh_token = "old-refresh-token"

		mock_decode_refresh_token.return_value = "test@example.com"
		mock_get_user.return_value = self.user

		mock_create_access_token.return_value = "new-access-token"
		mock_create_refresh_token.return_value = "new-refresh-token"

		result = await refresh_token( credentials=credentials, db=self.db, )

		self.assertEqual( result,
				{ "access_token": "new-access-token", "refresh_token": "new-refresh-token", "token_type": "bearer",
						}, )

		mock_decode_refresh_token.assert_awaited_once_with( "old-refresh-token", )

		mock_get_user.assert_awaited_once_with( email="test@example.com", db=self.db, )

		mock_update_token.assert_awaited_once_with( user=self.user, token="new-refresh-token", db=self.db, )

	@patch( "src.routes.auth.users_repository.update_token", new_callable=AsyncMock, )
	@patch( "src.routes.auth.users_repository.get_user_by_email", new_callable=AsyncMock, )
	@patch( "src.routes.auth.auth_service.decode_refresh_token", new_callable=AsyncMock, )
	async def test_refresh_token_invalid( self, mock_decode_refresh_token, mock_get_user, mock_update_token, ):
		credentials = SimpleNamespace( credentials="incorrect-refresh-token", )

		self.user.refresh_token = "stored-refresh-token"

		mock_decode_refresh_token.return_value = "test@example.com"
		mock_get_user.return_value = self.user

		with self.assertRaises( HTTPException ) as error:
			await refresh_token( credentials=credentials, db=self.db, )

		self.assertEqual( error.exception.status_code, 401, )

		self.assertEqual( error.exception.detail, "Invalid refresh token", )

		mock_update_token.assert_awaited_once_with( user=self.user, token=None, db=self.db, )

	# ------------------------------------------------------------------
	# avatar
	# ------------------------------------------------------------------

	@patch( "src.routes.auth.redis_client.delete", new_callable=AsyncMock, )
	@patch( "src.routes.auth.users_repository.update_avatar", new_callable=AsyncMock, )
	@patch( "src.routes.auth.cloudinary.CloudinaryImage", )
	@patch( "src.routes.auth.uploader.upload", )
	@patch( "src.routes.auth.cloudinary.config", )
	async def test_update_avatar_user( self,
			mock_cloudinary_config,
			mock_upload,
			mock_cloudinary_image,
			mock_update_avatar,
			mock_redis_delete, ):
		file = SimpleNamespace( file=MagicMock(), )

		mock_upload.return_value = { "version": 123,
				}

		mock_cloudinary_image.return_value.build_url.return_value = ("https://example.com/avatar.png")

		mock_update_avatar.return_value = self.user

		result = await update_avatar_user( file=file, current_user=self.user, db=self.db, )

		self.assertEqual( result, self.user, )

		mock_cloudinary_config.assert_called_once()

		mock_upload.assert_called_once_with( file.file, public_id="NotesApp/test_user", overwrite=True, )

		mock_cloudinary_image.assert_called_once_with( "NotesApp/test_user", )

		mock_cloudinary_image.return_value.build_url.assert_called_once_with( width=250,
				height=250,
				crop="fill",
				version=123, )

		mock_update_avatar.assert_awaited_once_with( "test@example.com", "https://example.com/avatar.png", self.db, )

		mock_redis_delete.assert_awaited_once_with( "access_token:test@example.com", )
