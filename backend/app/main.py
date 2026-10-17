"""
TRIAGEAI Backend Application Entrypoint.
FastAPI Application for Multimodal Emergency Triage Decision Support.
"""
import os

# Automatically load .env file into os.environ
def _load_env():
    env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k:
                        os.environ[k] = v

_load_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .api.router import api_router
from .services.triage_service import TriageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-initialize service and models
    print("[Startup] Initializing TRIAGEAI core services...")
    triage_svc = TriageService.get_instance()
    print(f"[Startup] Models ready status: Clinical={triage_svc.clinical_service.is_ready}, "
          f"ECG={triage_svc.ecg_service.is_ready}, XRay={triage_svc.xray_service.is_ready}")
    yield
    print("[Shutdown] Cleaning up resources...")


app = FastAPI(
    title="TRIAGEAI: AI-Assisted Multimodal Emergency Triage API",
    description="Research-Grade Multimodal Decision-Support Platform combining Clinical Vitals, ECG, and Chest Radiography.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "system": "TRIAGEAI",
        "subtitle": "AI-Assisted Multimodal Emergency Triage",
        "status": "operational",
        "version": "1.0.0",
        "docs_url": "/docs",
        "disclaimer": "AI-assisted research prototype intended for decision support. Not a substitute for professional medical judgment."
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
