import cloudinary
from cloudinary import uploader
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, Security, status, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.database.db import get_db
from src.database.redis import redis_client
from src.entity.models import User
from src.repository import users as users_repository
from src.schemas.token import TokenShema
from src.schemas.user import UserCreateSchema, UserResponseSchema
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter( prefix="/auth", tags=[ "auth" ], )
get_refresh_token = HTTPBearer()


@router.post( "/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED, )
async def signup( body: UserCreateSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends( get_db ) ):
	"""
	Register a new user.

	A verification email is scheduled and the user's password is hashed
	before the account is persisted.

	:param body: Validated user registration data.
	:param bt: FastAPI background task manager.
	:param request: Current HTTP request.
	:param db: Asynchronous database session.
	:return: Newly created user.
	:raises HTTPException: If an account with the same email already exists.
	"""
	exist_user = await users_repository.get_user_by_email( email=body.email, db=db )
	if exist_user:
		raise HTTPException( status_code=status.HTTP_409_CONFLICT, detail="Account already exists", )
	bt.add_task( send_email, body.email, body.user_name, str( request.base_url ) )
	body.password = auth_service.get_password_hash( body.password )
	new_user = await users_repository.create_user( body=body, db=db )
	return new_user


@router.post( "/login", response_model=TokenShema )
async def login( body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends( get_db ) ):
	"""
	Authenticate a user and issue JWT access and refresh tokens.

	:param body: OAuth2 login form containing email and password.
	:param db: Asynchronous database session.
	:return: Access token, refresh token, and token type.
	:raises HTTPException: If the user, email confirmation, or password is invalid.
	"""
	user = await users_repository.get_user_by_email( email=body.username, db=db )
	if user is None:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email", )
	if not user.confirmed:
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed", )
	if not auth_service.verify_password( body.password, user.password ):
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password", )
	# Generate JWT
	access_token = await auth_service.create_access_token( data={ "sub": user.email } )
	refresh_token = await auth_service.create_refresh_token( data={ "sub": user.email } )
	await users_repository.update_token( user=user, token=refresh_token, db=db )
	return { "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer",
	         }


@router.get( "/refresh_token" )
async def refresh_token( credentials: HTTPAuthorizationCredentials = Security( get_refresh_token ),
                         db: AsyncSession = Depends( get_db ), ):
	"""
	Issue a new access and refresh token pair.

	:param credentials: HTTP bearer credentials containing the refresh token.
	:param db: Asynchronous database session.
	:return: New access token, refresh token, and token type.
	:raises HTTPException: If the refresh token is invalid.
	"""
	token = credentials.credentials
	email = await auth_service.decode_refresh_token( token )
	user = await users_repository.get_user_by_email( email=email, db=db )
	if user.refresh_token != token:
		await users_repository.update_token( user=user, token=None, db=db )
		raise HTTPException( status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token", )

	access_token = await auth_service.create_access_token( data={ "sub": email } )
	refresh_token = await auth_service.create_refresh_token( data={ "sub": email } )
	await users_repository.update_token( user=user, token=refresh_token, db=db )
	return { "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer",
	         }


@router.patch( '/avatar', response_model=UserResponseSchema )
async def update_avatar_user( file: UploadFile = File(),
                              current_user: User = Depends( auth_service.get_current_user ),
                              db: AsyncSession = Depends( get_db ), ):
	"""
	Upload and update the authenticated user's avatar.

	The image is uploaded to Cloudinary and the cached authenticated user
	is invalidated after the avatar URL is updated.

	:param file: Uploaded image file.
	:param current_user: Currently authenticated user.
	:param db: Asynchronous database session.
	:return: Updated user.
	"""
	cloudinary.config( cloud_name=config.CLOUDINARY_CLOUD_NAME,
	                   api_key=config.CLOUDINARY_API_KEY,
	                   api_secret=config.CLOUDINARY_API_SECRET,
	                   secure=True, )

	r = uploader.upload( file.file, public_id=f'NotesApp/{current_user.user_name}', overwrite=True )
	src_url = cloudinary.CloudinaryImage( f'NotesApp/{current_user.user_name}' ).build_url( width=250,
	                                                                                        height=250,
	                                                                                        crop='fill',
	                                                                                        version=r.get( 'version',
	                                                                                                       ), )
	user = await users_repository.update_avatar( current_user.email, src_url, db )
	await redis_client.delete( f"access_token:{current_user.email}" )
	return user
