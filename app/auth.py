"""
Authentication helpers and Keycloak JWT integration.

This module provides JWT token verification using Keycloak's public keys (JWKS).
Production authentication only - JWT tokens required.
"""
from typing import Optional, Dict, Any
import os
import time
import requests
from jose import jwt
from jose.exceptions import JWTError
from .logging_config import get_logger

logger = get_logger(__name__)

# Configuration via environment variables
KEYCLOAK_JWKS_URL = os.getenv('KEYCLOAK_JWKS_URL')
KEYCLOAK_AUDIENCE = os.getenv('KEYCLOAK_AUDIENCE')
KEYCLOAK_ISSUER = os.getenv('KEYCLOAK_ISSUER')

# Simple cache for JWKS to avoid fetching on every request
_JWKS_CACHE: Dict[str, Any] = {"keys": None, "fetched_at": 0}
JWKS_CACHE_TTL = 60 * 60  # 1 hour


def _fetch_jwks(jwks_url: str):
    now = time.time()
    if _JWKS_CACHE.get('keys') and now - _JWKS_CACHE.get('fetched_at', 0) < JWKS_CACHE_TTL:
        return _JWKS_CACHE['keys']
    r = requests.get(jwks_url, timeout=5)
    r.raise_for_status()
    jwks = r.json()
    _JWKS_CACHE['keys'] = jwks
    _JWKS_CACHE['fetched_at'] = now
    return jwks


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT using Keycloak JWKS. Returns the token claims dict on success or None on failure.

    This function expects the following env vars if used:
    - KEYCLOAK_JWKS_URL
    - KEYCLOAK_AUDIENCE (optional)
    - KEYCLOAK_ISSUER (optional)
    """
    if not KEYCLOAK_JWKS_URL:
        logger.debug("KEYCLOAK_JWKS_URL not set; token verification skipped")
        return None
    try:
        jwks = _fetch_jwks(KEYCLOAK_JWKS_URL)
        # jose.jwt.decode will fetch the key from jwks automatically when provided as jwks
        # Note: audience and issuer validation is optional unless explicitly set via env vars
        claims = jwt.decode(
            token,
            jwks,
            audience=KEYCLOAK_AUDIENCE,  # None if not set (skips audience validation)
            issuer=KEYCLOAK_ISSUER,  # None if not set (skips issuer validation)
            options={"verify_aud": bool(KEYCLOAK_AUDIENCE)}  # Only verify audience if set
        )
        logger.info(f"Token verified successfully. User: {claims.get('preferred_username')}, Roles: {claims.get('realm_access', {}).get('roles', [])}")
        return claims
    except JWTError as e:
        # JWT verification failed (bad signature, expired, invalid claims)
        logger.warning(f"JWT verification failed: {str(e)}")
        return None
    except requests.RequestException as e:
        # JWKS fetch failed; log if needed, return None
        logger.error(f"Failed to fetch JWKS from {KEYCLOAK_JWKS_URL}: {str(e)}")
        return None
    except Exception as e:
        # Any other error; return None to let upstream handle unauthenticated response
        logger.error(f"Unexpected error during token verification: {str(e)}")
        return None


def parse_authorization_header(authorization: Optional[str]):
    if not authorization:
        return None
    if authorization.lower().startswith('bearer '):
        return authorization.split(' ', 1)[1].strip()
    return None

# Real Keycloak integration notes (summary):
# - Use python-jose to decode/verify JWTs using Keycloak's JWKS endpoint.
# - Validate token audience, issuer, expiration and required roles/realm_access.
# - Map Keycloak user info to application User entity and record tenant claim if present.
