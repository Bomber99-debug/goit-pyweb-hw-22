from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path( __file__ ).resolve().parent.parent.parent


class Settings( BaseSettings ):
	""" DB connection config """
	DB_URL: str = "sqlite:///db.sqlite3"

	""" JWT config """
	SECRET_KEY_JWT: str = ""
	ALGORITHM: str = "HS256"

	""" Mail config """
	MAIL_USER: str = "test"
	MAIL_PASSWORD: str = "test"
	MAIL_FROM: str = "admin@web.com"
	MAIL_SERVER: str = "localhost"
	MAIL_FROM_NAME: str = "test"
	MAIL_PORT: int = 1025
	MAIL_STARTTLS: bool = False
	MAIL_SSL_TLS: bool = False
	USE_CREDENTIALS: bool = True
	VALIDATE_CERTS: bool = True
	TEMPLATE_FOLDER: Path = BASE_DIR / "src" / "services" / "templates"

	""" Redis config """
	REDIS_USER: str = "default"
	REDIS_PASSWORD: str = "123456"
	REDIS_HOST_IP: str = "127.0.0.1"
	REDIS_PORT: int = 6379
	REDIS_DB: int = 0
	REDIS_URL: str = f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST_IP}:{REDIS_PORT}/{REDIS_DB}"

	""" Cloudinary config """
	CLOUDINARY_CLOUD_NAME: str = "my_cloud_name"
	CLOUDINARY_API_KEY: str = "my_key"
	CLOUDINARY_API_SECRET: str = "my_secret"

	@field_validator( "ALGORITHM" )
	@classmethod
	def validate_algorithm( cls, v: str ):
		if v not in [ "HS256", "HS384", "HS512" ]:
			raise ValueError( "Algorithm must be HS256 or HS384 or HS512" )
		return v

	model_config = SettingsConfigDict( extra="ignore", env_file=".env", env_file_encoding="utf-8" )


config = Settings()
