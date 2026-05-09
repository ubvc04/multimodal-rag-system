"""Authentication routes."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
	create_access_token,
	create_refresh_token,
	decode_token,
	get_current_active_user,
	get_password_hash,
	verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, TokenWithRefresh, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
	"/register",
	response_model=TokenWithRefresh,
	status_code=status.HTTP_201_CREATED,
	summary="Register a new user",
	description="Create a new user and return access + refresh tokens.",
	response_description="Tokens issued for the newly created user.",
)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> TokenWithRefresh:
	"""Register a new user with email/password."""
	existing = await db.execute(select(User).where(User.email == payload.email))
	if existing.scalar_one_or_none() is not None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

	user = User(
		email=payload.email,
		hashed_password=get_password_hash(payload.password),
		full_name=payload.full_name,
	)
	db.add(user)
	await db.flush()
	await db.refresh(user)

	access_token = create_access_token({"sub": user.email})
	refresh_token = create_refresh_token({"sub": user.email})

	return TokenWithRefresh(
		access_token=access_token,
		refresh_token=refresh_token,
		token_type="bearer",
		expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
	)


@router.post(
	"/login",
	response_model=TokenWithRefresh,
	status_code=status.HTTP_200_OK,
	summary="Login with email and password",
	description="Verify credentials and return access + refresh tokens.",
	response_description="Tokens issued for the authenticated user.",
)
async def login_user(
	response: Response,
	form_data: OAuth2PasswordRequestForm = Depends(),
	db: AsyncSession = Depends(get_db),
) -> TokenWithRefresh:
	"""Authenticate a user and issue tokens."""
	result = await db.execute(select(User).where(User.email == form_data.username))
	user = result.scalar_one_or_none()
	if user is None or not verify_password(form_data.password, user.hashed_password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	access_token = create_access_token({"sub": user.email})
	refresh_token = create_refresh_token({"sub": user.email})

	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=not settings.DEBUG,
		samesite="lax",
		max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
		path="/",
	)

	return TokenWithRefresh(
		access_token=access_token,
		refresh_token=refresh_token,
		token_type="bearer",
		expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
	)


@router.post(
	"/refresh",
	response_model=Token,
	status_code=status.HTTP_200_OK,
	summary="Refresh access token",
	description="Use refresh token cookie to issue a new access token.",
	response_description="New access token for the user.",
)
async def refresh_access_token(request: Request) -> Token:
	"""Issue a new access token from refresh token cookie."""
	refresh_token = request.cookies.get("refresh_token")
	if not refresh_token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

	payload = decode_token(refresh_token)
	if payload["type"] != "refresh":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

	access_token = create_access_token({"sub": payload["sub"]})
	return Token(access_token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post(
	"/logout",
	status_code=status.HTTP_200_OK,
	summary="Logout",
	description="Clear refresh token cookie.",
	response_description="Logout confirmation.",
)
async def logout_user(response: Response) -> dict:
	"""Clear refresh token cookie."""
	response.delete_cookie(key="refresh_token", path="/")
	return {"detail": "Logged out"}


@router.get(
	"/me",
	response_model=UserResponse,
	status_code=status.HTTP_200_OK,
	summary="Get current user profile",
	description="Return profile details for the current user.",
	response_description="Current user profile.",
)
async def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
	"""Return the current authenticated user's profile."""
	return UserResponse.model_validate(current_user)
