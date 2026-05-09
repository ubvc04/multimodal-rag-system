"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import agent, auth, documents, health, query

router = APIRouter()
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(query.router)
router.include_router(agent.router)
router.include_router(health.router)
