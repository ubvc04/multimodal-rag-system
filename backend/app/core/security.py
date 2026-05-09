"""Security utilities for JWT auth."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify a plaintext password against its hash."""
	return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
	"""Hash a plaintext password."""
	return pwd_context.hash(password)


def _build_token_payload(data: dict, token_type: str, expires_delta: timedelta) -> dict:
	issued_at = datetime.now(timezone.utc)
	expire = issued_at + expires_delta
	payload = {
		"sub": data.get("sub"),
		"iat": int(issued_at.timestamp()),
		"exp": int(expire.timestamp()),
		"type": token_type,
	}
	return payload


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
	"""Create an access JWT."""
	expire = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	payload = _build_token_payload(data, "access", expire)
	return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
	"""Create a refresh JWT."""
	expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
	payload = _build_token_payload(data, "refresh", expire)
	return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
	"""Decode and validate a JWT."""
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
	except JWTError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

	token_type = payload.get("type")
	if token_type not in {"access", "refresh"}:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
	subject = payload.get("sub")
	if not subject:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

	return {
		"sub": str(subject),
		"exp": int(payload.get("exp")),
		"iat": int(payload.get("iat")),
		"type": str(token_type),
	}


async def get_current_user(
	token: str = Depends(oauth2_scheme),
	db: AsyncSession = Depends(get_db),
) -> User:
	"""Retrieve current user from access token."""
	payload = decode_token(token)
	if payload["type"] != "access":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
	result = await db.execute(select(User).where(User.email == payload["sub"]))
	user = result.scalar_one_or_none()
	if user is None or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")

	return user


async def get_current_active_user(
	current_user: User = Depends(get_current_user),
) -> User:
	"""Ensure the current user is active."""
	if not current_user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
	return current_user
