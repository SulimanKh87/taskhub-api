from fastapi import FastAPI  # FastAPI main framework
from fastapi.middleware.cors import CORSMiddleware  # Enables CORS for frontend calls
from fastapi.middleware.trustedhost import TrustedHostMiddleware  # Prevents Host header attacks

from app.config import settings  # Load app configuration
from app.database import connect_to_mongo, close_mongo_connection  # DB connection handlers
from app.routes import auth, tasks  # Import route modules

# Initialize FastAPI app with title and debug mode from config
app = FastAPI(title=settings.app_name, debug=settings.app_debug)

# === Database Lifecycle Events ===
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
# === Security Middleware ===
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.local", "taskhub-api", "test"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Cross-Origin Resource Sharing for local development or frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],  # Allowed frontend URLs
    allow_credentials=True,   # Allow cookies/auth headers
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],      # Allow all headers (Authorization, Content-Type, etc.)
)

# === Routers ===
# Add authentication and task routes to the FastAPI app
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# === Health Check Endpoint ===
# Useful for monitoring, Docker health checks, and uptime probes
@app.get("/health")
async def health_check():
    # Returns minimal information to confirm API is running
    return {"status": "ok", "app": settings.app_name}
