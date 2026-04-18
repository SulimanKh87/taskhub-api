# app/main.py
"""
FastAPI application entrypoint.

- App creation
- Middleware registration
- Router wiring
- Health check
- Prometheus metrics endpoint (/metrics)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.routes import auth, tasks

# -----------------------------------------------------------------------
# Prometheus metrics
# prometheus-fastapi-instrumentator automatically tracks:
#   - http_requests_total         (counter, by method + path + status)
#   - http_request_duration_seconds (histogram, by method + path)
#   - http_requests_in_progress   (gauge, by method + path)
#
# These are the metrics Grafana will visualize.
#
# WHY NOT EXPOSE /metrics TO THE INTERNET?
#   In production, /metrics should be on an internal port or behind
#   a network policy. For this project it's on the main port for simplicity.
#   On ECS/K8s you'd restrict access via security group / NetworkPolicy.
# -----------------------------------------------------------------------
from prometheus_fastapi_instrumentator import Instrumentator


# ------------------------------------------------------------
# Security headers middleware
# ------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
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
# Middleware (order matters — applied bottom-up)
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
# Prometheus instrumentation
# Must be set up AFTER app is created and BEFORE first request
# expose() registers the /metrics route automatically
# ------------------------------------------------------------
Instrumentator(
    should_group_status_codes=True,  # group 2xx, 4xx, 5xx
    should_ignore_untemplated=True,  # skip unmatched routes (reduces cardinality)
    should_respect_env_var=True,  # disable with ENABLE_METRICS=false
    env_var_name="ENABLE_METRICS",
    excluded_handlers=["/metrics"],  # don't track /metrics calls themselves
).instrument(app).expose(app)


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
