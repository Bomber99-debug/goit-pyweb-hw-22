from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr, NameEmail

from src.conf.config import config
from src.services.auth import auth_service

mail_config = ConnectionConfig( MAIL_USERNAME=config.MAIL_USER,
                                MAIL_PASSWORD=config.MAIL_PASSWORD,
                                MAIL_FROM=config.MAIL_FROM,
                                MAIL_PORT=config.MAIL_PORT,
                                MAIL_SERVER=config.MAIL_SERVER,
                                MAIL_STARTTLS=config.MAIL_STARTTLS,
                                MAIL_SSL_TLS=config.MAIL_SSL_TLS,
                                USE_CREDENTIALS=config.USE_CREDENTIALS,
                                TEMPLATE_FOLDER=config.TEMPLATE_FOLDER, )


async def send_email( email: EmailStr, username: str, host: str ):
	"""
	Send an email verification message to a user.

	A temporary JWT verification token is generated and included
	in the verification email template.

	:param email: Recipient email address.
	:param username: Recipient user name.
	:param host: Base URL of the application.
	:return: None.
	"""
	try:
		token_verification = auth_service.create_email_token( { "sub": email } )
		message = MessageSchema( subject="Email Verification",
		                         recipients=[ NameEmail( name=username, email=email ) ],
		                         template_body={ "host": host, "username": username, "token": token_verification },
		                         subtype=MessageType.html, )
		fm = FastMail( config=mail_config )
		await fm.send_message( message, template_name="verify_email.html" )
	except ConnectionError as err:
		print( err )


async def send_email_add_contact( email_user: str,
                                  user_name: str,
                                  email_contact: str,
                                  first_name: str,
                                  last_name: str,
                                  phones: list, ):
	"""
	Send a notification email after a new contact is created.

	:param email_user: Email address of the contact owner.
	:param user_name: Name of the contact owner.
	:param email_contact: Email address of the newly created contact.
	:param first_name: First name of the new contact.
	:param last_name: Last name of the new contact.
	:param phones: Phone numbers associated with the new contact.
	:return: None.
	"""
	username = f'{first_name} {last_name}'
	try:
		message = MessageSchema( subject="Add Contact",
		                         recipients=[ NameEmail( name=user_name, email=email_user ) ],
		                         template_body={ "username": username, "email": email_contact, "phones": phones },
		                         subtype=MessageType.html, )
		fm = FastMail( config=mail_config )
		await fm.send_message( message, template_name="add_contact.html" )
	except ConnectionError as err:
		print( err )
