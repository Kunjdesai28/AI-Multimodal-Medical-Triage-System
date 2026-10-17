"""
API Router Aggregator.
"""
from fastapi import APIRouter
from .routes import health, clinical, ecg, xray, assessment, timeline, metrics, auth

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(clinical.router)
api_router.include_router(ecg.router)
api_router.include_router(xray.router)
api_router.include_router(assessment.router)
api_router.include_router(timeline.router)
api_router.include_router(metrics.router)
