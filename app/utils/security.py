from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_days)
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)
