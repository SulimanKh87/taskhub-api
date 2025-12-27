# app/main.py

"""
FastAPI application entrypoint.

- App creation
- Middleware registration
- Router wiring
- Health check

Database connections are handled lazily via SQLAlchemy sessions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.routes import auth, tasks


# ------------------------------------------------------------
# Application setup
# ------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)


# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Routers
# ------------------------------------------------------------
app.include_router(auth.router, tags=["auth"])
app.include_router(tasks.router, tags=["tasks"])


# ------------------------------------------------------------
# Health check
# ------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
    }
