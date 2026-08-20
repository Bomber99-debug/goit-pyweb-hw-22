from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.email import (send_email, send_email_add_contact,
                                )


class TestEmailService( IsolatedAsyncioTestCase ):

	@patch( "src.services.email.FastMail", )
	@patch( "src.services.email.auth_service.create_email_token", )
	async def test_send_email_success( self, mock_create_email_token, mock_fast_mail, ):
		mock_create_email_token.return_value = "verification-token"

		fast_mail_instance = MagicMock()
		fast_mail_instance.send_message = AsyncMock()

		mock_fast_mail.return_value = fast_mail_instance

		await send_email( email="test@example.com", username="test_user", host="http://testserver/", )

		mock_create_email_token.assert_called_once_with( { "sub": "test@example.com",
				}, )

		mock_fast_mail.assert_called_once()

		fast_mail_instance.send_message.assert_awaited_once()

		call_args = fast_mail_instance.send_message.await_args

		self.assertEqual( call_args.kwargs[ "template_name" ], "verify_email.html", )

	@patch( "builtins.print", )
	@patch( "src.services.email.FastMail", )
	@patch( "src.services.email.auth_service.create_email_token", )
	async def test_send_email_connection_error( self, mock_create_email_token, mock_fast_mail, mock_print, ):
		mock_create_email_token.return_value = "verification-token"

		fast_mail_instance = MagicMock()
		fast_mail_instance.send_message = AsyncMock( side_effect=ConnectionError( "Mail server unavailable", ), )

		mock_fast_mail.return_value = fast_mail_instance

		await send_email( email="test@example.com", username="test_user", host="http://testserver/", )

		mock_print.assert_called_once()

	@patch( "src.services.email.FastMail", )
	async def test_send_email_add_contact_success( self, mock_fast_mail, ):
		fast_mail_instance = MagicMock()
		fast_mail_instance.send_message = AsyncMock()

		mock_fast_mail.return_value = fast_mail_instance

		await send_email_add_contact( email_user="owner@example.com",
				user_name="owner",
				email_contact="contact@example.com",
				first_name="John",
				last_name="Doe",
				phones=[ "+380991112233",
						], )

		mock_fast_mail.assert_called_once()

		fast_mail_instance.send_message.assert_awaited_once()

		call_args = fast_mail_instance.send_message.await_args

		self.assertEqual( call_args.kwargs[ "template_name" ], "add_contact.html", )

	@patch( "builtins.print", )
	@patch( "src.services.email.FastMail", )
	async def test_send_email_add_contact_connection_error( self, mock_fast_mail, mock_print, ):
		fast_mail_instance = MagicMock()

		fast_mail_instance.send_message = AsyncMock( side_effect=ConnectionError( "Mail server unavailable", ), )

		mock_fast_mail.return_value = fast_mail_instance

		await send_email_add_contact( email_user="owner@example.com",
				user_name="owner",
				email_contact="contact@example.com",
				first_name="John",
				last_name="Doe",
				phones=[ "+380991112233",
						], )

		mock_print.assert_called_once()
