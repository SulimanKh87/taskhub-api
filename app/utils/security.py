from jose import JWTError, jwt                 # JWT for token creation and validation
from datetime import datetime, timedelta       # Used for token expiration
from passlib.context import CryptContext        # Provides password hashing
from app.config import settings                 # Load JWT secret, algorithm, and expiry

# Initialize password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================
# Password Hashing Utilities
# ==========================

def hash_password(password: str):
    """Hash a plain password securely."""
    return pwd_context.hash(password)           # Returns a bcrypt-hashed version


def verify_password(plain: str, hashed: str):
    """Verify that a plain password matches the stored hash."""
    return pwd_context.verify(plain, hashed)


# ==========================
# JWT Token Creation
# ==========================

def create_access_token(data: dict):
    """Generate short-lived access JWT token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    data.update({"exp": expire})                # Add expiration claim
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict):
    """Generate long-lived refresh JWT token."""
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_days)
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)
