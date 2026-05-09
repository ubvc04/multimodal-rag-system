"""Authentication API tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_success(async_client):
	response = await async_client.post(
		"/api/v1/auth/register",
		json={"email": "new@example.com", "password": "password123", "full_name": "New User"},
	)
	assert response.status_code == 201
	body = response.json()
	assert "access_token" in body


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client):
	await async_client.post(
		"/api/v1/auth/register",
		json={"email": "dup@example.com", "password": "password123", "full_name": "Dup User"},
	)
	response = await async_client.post(
		"/api/v1/auth/register",
		json={"email": "dup@example.com", "password": "password123", "full_name": "Dup User"},
	)
	assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(async_client, test_user):
	response = await async_client.post(
		"/api/v1/auth/login",
		data={"username": test_user.email, "password": "password123"},
	)
	assert response.status_code == 200
	body = response.json()
	assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client, test_user):
	response = await async_client.post(
		"/api/v1/auth/login",
		data={"username": test_user.email, "password": "wrong"},
	)
	assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(async_client, test_user):
	login = await async_client.post(
		"/api/v1/auth/login",
		data={"username": test_user.email, "password": "password123"},
	)
	assert login.status_code == 200
	response = await async_client.post("/api/v1/auth/refresh", cookies=login.cookies)
	assert response.status_code == 200
	assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client, auth_headers):
	response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
	assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client):
	response = await async_client.get("/api/v1/auth/me")
	assert response.status_code == 401
