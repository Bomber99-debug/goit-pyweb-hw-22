from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.responses import FileResponse

from src.routes.email import (
	confirm_email,
	request_verification_email,
	track_email_open,
)


class TestEmailRoutes(IsolatedAsyncioTestCase):

	def setUp(self):
		self.db = MagicMock()

		self.user = SimpleNamespace(
			id=1,
			email="test@example.com",
			user_name="test_user",
			confirmed=False,
		)

	# ---------------------------------------------------------------
	# confirm_email
	# ---------------------------------------------------------------

	@patch(
		"src.routes.email.repository_email.confirmed_email",
		new_callable=AsyncMock,
	)
	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	@patch(
		"src.routes.email.auth_service.get_email_from_token",
		new_callable=AsyncMock,
	)
	async def test_confirm_email_success(
		self,
		mock_get_email_from_token,
		mock_get_user,
		mock_confirmed_email,
	):
		mock_get_email_from_token.return_value = "test@example.com"
		mock_get_user.return_value = self.user

		result = await confirm_email(
			token="verification-token",
			db=self.db,
		)

		self.assertEqual(
			result,
			{
				"message": "Email address confirmed",
			},
		)

		mock_get_email_from_token.assert_awaited_once_with(
			"verification-token",
		)

		mock_get_user.assert_awaited_once_with(
			"test@example.com",
			self.db,
		)

		mock_confirmed_email.assert_awaited_once_with(
			"test@example.com",
			self.db,
		)

	@patch(
		"src.routes.email.repository_email.confirmed_email",
		new_callable=AsyncMock,
	)
	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	@patch(
		"src.routes.email.auth_service.get_email_from_token",
		new_callable=AsyncMock,
	)
	async def test_confirm_email_already_confirmed(
		self,
		mock_get_email_from_token,
		mock_get_user,
		mock_confirmed_email,
	):
		self.user.confirmed = True

		mock_get_email_from_token.return_value = "test@example.com"
		mock_get_user.return_value = self.user

		result = await confirm_email(
			token="verification-token",
			db=self.db,
		)

		self.assertEqual(
			result,
			{
				"message": "Email address already confirmed",
			},
		)

		mock_confirmed_email.assert_not_awaited()

	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	@patch(
		"src.routes.email.auth_service.get_email_from_token",
		new_callable=AsyncMock,
	)
	async def test_confirm_email_user_not_found(
		self,
		mock_get_email_from_token,
		mock_get_user,
	):
		mock_get_email_from_token.return_value = "missing@example.com"
		mock_get_user.return_value = None

		with self.assertRaises(
			HTTPException,
		) as error:
			await confirm_email(
				token="verification-token",
				db=self.db,
			)

		self.assertEqual(
			error.exception.status_code,
			400,
		)

		self.assertEqual(
			error.exception.detail,
			"Verification error",
		)

	# ---------------------------------------------------------------
	# request_verification_email
	# ---------------------------------------------------------------

	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	async def test_request_verification_email_success(
		self,
		mock_get_user,
	):
		body = SimpleNamespace(
			email="test@example.com",
		)

		background_tasks = MagicMock()

		request = SimpleNamespace(
			base_url="http://testserver/",
		)

		mock_get_user.return_value = self.user

		result = await request_verification_email(
			body=body,
			background_tasks=background_tasks,
			request=request,
			db=self.db,
		)

		self.assertEqual(
			result,
			{
				"message": "Verification email sent",
			},
		)

		mock_get_user.assert_awaited_once_with(
			"test@example.com",
			self.db,
		)

		background_tasks.add_task.assert_called_once()

		call_args = background_tasks.add_task.call_args

		self.assertEqual(
			call_args.args[1],
			"test@example.com",
		)

		self.assertEqual(
			call_args.args[2],
			"test_user",
		)

		self.assertEqual(
			call_args.args[3],
			"http://testserver/",
		)

	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	async def test_request_verification_email_already_confirmed(
		self,
		mock_get_user,
	):
		self.user.confirmed = True

		body = SimpleNamespace(
			email="test@example.com",
		)

		background_tasks = MagicMock()

		request = SimpleNamespace(
			base_url="http://testserver/",
		)

		mock_get_user.return_value = self.user

		result = await request_verification_email(
			body=body,
			background_tasks=background_tasks,
			request=request,
			db=self.db,
		)

		self.assertEqual(
			result,
			{
				"message": "Email address already confirmed",
			},
		)

		background_tasks.add_task.assert_not_called()

	@patch(
		"src.routes.email.repository_email.get_user_by_email",
		new_callable=AsyncMock,
	)
	async def test_request_verification_email_user_not_found(
		self,
		mock_get_user,
	):
		body = SimpleNamespace(
			email="missing@example.com",
		)

		background_tasks = MagicMock()

		request = SimpleNamespace(
			base_url="http://testserver/",
		)

		mock_get_user.return_value = None

		with self.assertRaises(
			HTTPException,
		) as error:
			await request_verification_email(
				body=body,
				background_tasks=background_tasks,
				request=request,
				db=self.db,
			)

		self.assertEqual(
			error.exception.status_code,
			404,
		)

		self.assertEqual(
			error.exception.detail,
			"User not found",
		)

		background_tasks.add_task.assert_not_called()

	# ---------------------------------------------------------------
	# track_email_open
	# ---------------------------------------------------------------

	@patch(
		"builtins.print",
	)
	async def test_track_email_open(
		self,
		mock_print,
	):
		response = MagicMock()

		result = await track_email_open(
			username="test_user",
			response=response,
			db=self.db,
		)

		self.assertIsInstance(
			result,
			FileResponse,
		)

		self.assertEqual(
			result.path,
			"src/static/open_check.png",
		)

		self.assertEqual(
			result.media_type,
			"image/png",
		)

		self.assertEqual(
			mock_print.call_count,
			3,
		)