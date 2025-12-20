"""
FastAPI application entrypoint.

Responsible for:
- App creation
- Middleware registration
- Router wiring
- Startup / shutdown lifecycle
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import auth, tasks

# -------------------------------------------------------------------
# Application setup
# -------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)


# -------------------------------------------------------------------
# Database lifecycle hooks
# -------------------------------------------------------------------
@app.on_event("startup")
async def startup_db():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db():
    # Avoid closing DB during CI test runs
    if os.getenv("ENV") != "test":
        await close_mongo_connection()


# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.local", "taskhub-api", "test"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------
# Auth routes (/auth/*)
app.include_router(auth.router, tags=["auth"])

# Task routes already include /tasks prefix internally
app.include_router(tasks.router, tags=["tasks"])


# -------------------------------------------------------------------
# Health check
# -------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
    }
