from pydantic import BaseModel


# ==========================
# AUTH / TOKEN SCHEMAS
# ==========================

class Token(BaseModel):
    """JWT response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT payload content."""
    sub: str
    exp: int
