"""Clerk JWT authentication middleware for FastAPI."""

from __future__ import annotations

import httpx
import jwt
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = structlog.get_logger()

security = HTTPBearer(auto_error=False)

# Cache for JWKS keys
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch Clerk's JWKS (JSON Web Key Set) for JWT verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    if not settings.CLERK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk is not configured",
        )

    # Clerk JWKS endpoint is derived from the publishable key
    # Format: https://<clerk-frontend-api>/.well-known/jwks.json
    pub_key = settings.CLERK_PUBLISHABLE_KEY
    frontend_api = pub_key.split("_")[-1] if pub_key else ""
    jwks_url = f"https://{frontend_api}/.well-known/jwks.json"

    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Verify the Clerk JWT and return the user payload.

    Returns a dict with at least 'sub' (user ID) and any other claims.
    """
    if not settings.CLERK_SECRET_KEY:
        # Auth not configured — allow requests through in development
        return {"sub": "dev-user", "email": "dev@shielded.app"}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwks = await _get_jwks()
        # Get the signing key from JWKS
        jwks_client = jwt.PyJWKClient.__new__(jwt.PyJWKClient)
        jwks_client.jwk_set = jwt.PyJWKSet.from_dict(jwks)

        # Decode the header to find the right key
        unverified_header = jwt.get_unverified_header(token)
        key = None
        for jwk_key in jwks_client.jwk_set.keys:
            if jwk_key.key_id == unverified_header.get("kid"):
                key = jwk_key.key
                break

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signing key",
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        await logger.awarning("Invalid JWT token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def require_auth():
    """Dependency that requires authentication.

    Usage:
        @router.get("/protected", dependencies=[Depends(require_auth())])
        async def protected_route():
            ...

    Or to access the user:
        @router.get("/me")
        async def get_me(user: dict = Depends(get_current_user)):
            return user
    """
    return Depends(get_current_user)
