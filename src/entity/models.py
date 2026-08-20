from datetime import date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, func, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base( DeclarativeBase ):
	"""Base declarative class for all SQLAlchemy ORM models."""

	...


class Contact( Base ):
	"""
	Represent a contact containing personal information and phone numbers.
	"""

	__tablename__ = "contacts"

	id: Mapped[ int ] = mapped_column( "id", primary_key=True, )
	first_name: Mapped[ str ] = mapped_column( "first_name", String( 50 ), index=True, nullable=False, )
	last_name: Mapped[ str ] = mapped_column( "last_name", String( 50 ), nullable=False, )
	email: Mapped[ str ] = mapped_column( "email", String( 250 ), )
	birthday: Mapped[ date ] = mapped_column( "birthday", Date, index=True, )
	notes: Mapped[ str | None ] = mapped_column( "notes", String( 1000 ), )

	phones: Mapped[ list[ "Phone" ] ] = relationship( back_populates="contact", cascade="all, delete-orphan", )

	created_at: Mapped[ date ] = mapped_column( "created_at", DateTime, default=func.now() )
	updated_at: Mapped[ date ] = mapped_column( "updated_at", DateTime, default=func.now(), onupdate=func.now(), )

	user_id: Mapped[ int ] = mapped_column( Integer, ForeignKey( "users.id" ), nullable=True )
	user: Mapped[ "User" ] = relationship( "User", backref="contacts", lazy="joined" )


class Phone( Base ):
	"""Represent a phone number associated with a contact."""

	__tablename__ = "phones"

	id: Mapped[ int ] = mapped_column( "id", primary_key=True, )
	number: Mapped[ str ] = mapped_column( "number", String( 13 ), index=True, nullable=False, unique=True, )
	contact_id: Mapped[ int ] = mapped_column( "contact_id", ForeignKey( "contacts.id" ), nullable=False, )

	contact: Mapped[ "Contact" ] = relationship( back_populates="phones", )

	created_at: Mapped[ date ] = mapped_column( "created_at", DateTime, default=func.now() )
	updated_at: Mapped[ date ] = mapped_column( "updated_at", DateTime, default=func.now(), onupdate=func.now(), )

	user_id: Mapped[ int ] = mapped_column( Integer, ForeignKey( "users.id" ), nullable=True )
	user: Mapped[ "User" ] = relationship( "User", backref="phones", lazy="joined" )


class User( Base ):
	"""Represent an application user and authentication-related data."""
	__tablename__ = "users"
	id: Mapped[ int ] = mapped_column( primary_key=True )
	user_name: Mapped[ str ] = mapped_column( "user_name", String( 255 ) )
	email: Mapped[ str ] = mapped_column( "email", String( 255 ), nullable=False, unique=True, )
	password: Mapped[ str ] = mapped_column( "password", nullable=False )
	avatar: Mapped[ str ] = mapped_column( "avatar", nullable=True )
	refresh_token: Mapped[ str ] = mapped_column( "refresh_token", String( 255 ), nullable=True, )

	created_at: Mapped[ date ] = mapped_column( "created_at", DateTime, default=func.now() )
	updated_at: Mapped[ date ] = mapped_column( "updated_at", DateTime, default=func.now(), onupdate=func.now(), )

	confirmed: Mapped[ bool ] = mapped_column( "confirmed", Boolean, default=False, nullable=False )
