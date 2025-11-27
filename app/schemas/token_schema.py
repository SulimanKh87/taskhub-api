from pydantic import BaseModel

# ==========================
# AUTH / TOKEN SCHEMAS
# ==========================


class Token(BaseModel):
    """JWT response schema."""

    # Defines what the API returns after a successful login or registration.
    access_token: str  # The short-lived access token
    refresh_token: str  # The longer-lived refresh token
    token_type: str = "bearer"  # Always 'bearer' for Authorization headers


class TokenPayload(BaseModel):
    """JWT payload content."""

    # Defines the structure of the JWT contents after decoding.
    sub: str  # Subject (usually the username)
    exp: int  # Expiration timestamp (Unix format)
