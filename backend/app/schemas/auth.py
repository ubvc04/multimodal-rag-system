"""Authentication schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import SettingsConfigDict


class UserCreate(BaseModel):
	"""User registration payload."""

	email: EmailStr
	password: str = Field(min_length=8)
	full_name: str


class UserResponse(BaseModel):
	"""User profile response."""

	id: UUID
	email: EmailStr
	full_name: str
	is_active: bool
	created_at: datetime

	model_config = SettingsConfigDict(from_attributes=True)


class Token(BaseModel):
	"""Access token response."""

	access_token: str
	token_type: str
	expires_in: int


class TokenWithRefresh(Token):
	"""Access token plus refresh token."""

	refresh_token: str


class LoginRequest(BaseModel):
	"""Email/password login payload."""

	email: EmailStr
	password: str
