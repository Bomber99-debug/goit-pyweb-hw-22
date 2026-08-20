from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pyrate_limiter import Duration, Limiter, Rate
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import email as repository_email
from src.schemas.email import RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email
from src.services.rate_limiter import RateLimiter

router = APIRouter( prefix="/email", tags=[ "email" ] )


@router.get( "/confirmed_email/{token}",
             dependencies=[ Depends( RateLimiter( limiter=Limiter( Rate( 1, Duration.SECOND * 5, ), ), ), ), ], )
async def confirm_email( token: str, db: AsyncSession = Depends( get_db ), ):
	mail = await auth_service.get_email_from_token( token )
	user = await repository_email.get_user_by_email( mail, db )
	if user is None:
		raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error" )
	if user.confirmed:
		return { "message": "Email address already confirmed" }
	await repository_email.confirmed_email( mail, db )
	return { "message": "Email address confirmed" }


@router.post( "/request_email" )
async def request_email( body: RequestEmail,
                         background_tasks: BackgroundTasks,
                         request: Request,
                         db: AsyncSession = Depends( get_db ), ):
	user = await repository_email.get_user_by_email( body.email, db )
	if not user:
		if user.confirmed:
			return { "message": "Email address already confirmed" }
		if user:
			background_tasks.add_task( send_email, user.email, user.user_name, str( request.base_url ) )
		return { "message": "Email address confirmed" }
	else:
		raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="User not found", )


@router.get( '/{username}' )
async def request_email( username: str, response: Response, db: AsyncSession = Depends( get_db ) ):
	print( '--------------------------------' )
	print( f'{username} зберігаємо що він відкрив email в БД' )
	print( '--------------------------------' )
	return FileResponse( "src/static/open_check.png", media_type="image/png", content_disposition_type="inline" )
