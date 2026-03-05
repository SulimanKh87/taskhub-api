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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.routes import auth, tasks

# SecurityHeadersMiddleware class
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

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

app.add_middleware(SecurityHeadersMiddleware)

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
