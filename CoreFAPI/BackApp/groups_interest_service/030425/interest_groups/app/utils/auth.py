# app/utils/auth.py
import os
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import logging
from datetime import datetime, timedelta
from functools import lru_cache
import json

logger = logging.getLogger("auth.service")

# Configuration Models
class AuthConfig(BaseModel):
    user_service_url: str
    jwt_public_key: str
    jwt_algorithm: str = "RS256"
    cache_ttl: int = 300  # 5 minutes

class UserClaims(BaseModel):
    sub: str  # user_id
    exp: datetime
    scopes: List[str] = []
    is_active: bool = True

class AuthenticatedUser(BaseModel):
    id: int
    username: str
    email: Optional[str]
    permissions: List[str] = []
    is_active: bool = True

# Cached configuration
@lru_cache()
def get_auth_config() -> AuthConfig:
    return AuthConfig(
        user_service_url=os.environ["AUTH_SERVICE_URL"],
        jwt_public_key=os.environ["JWT_PUBLIC_KEY"],
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "RS256")
    )

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=os.getenv("AUTH_TOKEN_URL", "/auth/token"),
    scopes={
        "groups.read": "Read access to groups",
        "groups.write": "Write access to groups"
    },
    auto_error=False
)

async def validate_jwt_token(token: str) -> UserClaims:
    """Validate JWT token with public key"""
    config = get_auth_config()
    try:
        payload = jwt.decode(
            token,
            config.jwt_public_key,
            algorithms=[config.jwt_algorithm],
            options={
                "verify_aud": False,
                "verify_iss": True,
                "verify_sub": True
            }
        )
        return UserClaims(**payload)
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTClaimsError as e:
        logger.warning(f"Invalid token claims: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token claims")
    except Exception as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def fetch_user_data(user_id: str, token: str) -> AuthenticatedUser:
    """Fetch user data from external service with caching"""
    config = get_auth_config()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": str(hash(token))[:8]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config.user_service_url}/users/{user_id}",
                headers=headers
            )
            response.raise_for_status()
            return AuthenticatedUser(**response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"User service error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Failed to fetch user data"
        )
    except Exception as e:
        logger.error(f"User service connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="User service unavailable"
        )

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
) -> AuthenticatedUser:
    """Dependency for getting current authenticated user"""
    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        # Validate token structure and signature
        claims = await validate_jwt_token(token)
        
        # Get additional user data
        user = await fetch_user_data(claims.sub, token)
        
        # Verify user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempt: {user.id}")
            raise HTTPException(status_code=403, detail="Inactive user")
            
        # Attach token claims to request state
        request.state.auth_claims = claims
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_current_active_user(
    user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Additional check for active users only"""
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user

def require_scope(required_scope: str):
    """Dependency factory for scope checking"""
    def checker(
        request: Request,
        user: AuthenticatedUser = Depends(get_current_active_user)
    ):
        claims: UserClaims = request.state.auth_claims
        if required_scope not in claims.scopes:
            logger.warning(f"Missing scope {required_scope} for user {user.id}")
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_scope} scope"
            )
        return user
    return checker

