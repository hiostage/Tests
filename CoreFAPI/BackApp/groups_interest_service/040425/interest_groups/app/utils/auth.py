import os
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger("auth.service")

# Configuration Models
class AuthConfig(BaseModel):
    auth_proxy_url: str  # URL для auth-proxy
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
        auth_proxy_url=os.environ["AUTH_PROXY_URL"],  # URL для auth-proxy
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
    """Проверка токена через auth-proxy"""
    config = get_auth_config()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.auth_proxy_url}/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            response.raise_for_status()
            data = response.json()
            
            return UserClaims(
                sub=data["sub"],
                exp=datetime.utcnow() + timedelta(hours=1),  # Примерное время экспирации
                scopes=data.get("permissions", []),
                is_active=data.get("is_active", True)
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Auth proxy error: {e.response.text}")
        raise HTTPException(status_code=401, detail="Token validation failed")

async def fetch_user_data(user_id: str, token: str) -> AuthenticatedUser:
    """Fetch user data from AUTH_PROXY_URL with caching"""
    config = get_auth_config()

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": str(hash(token))[:8]
        # "X-Service-Token": config.service_auth_token 
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Используем AUTH_PROXY_URL для получения данных о пользователе
            response = await client.get(
                f"{config.AUTH_PROXY_URL}/users/{user_id}",
                headers=headers
            )
            response.raise_for_status()
            return AuthenticatedUser(**response.json())

    except httpx.HTTPStatusError as e:
        logger.error(f"User service error ({e.response.status_code}): {e.response.text}")

        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")

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
    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Получаем данные напрямую из auth-proxy
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{get_auth_config().auth_proxy_url}/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            user_data = response.json()
            
            return AuthenticatedUser(
                id=int(user_data["sub"]),
                username=user_data["username"],
                email=user_data.get("email"),
                permissions=user_data.get("permissions", []),
                is_active=user_data.get("is_active", True)
            )
            
    except Exception as e:
        logger.error(f"Auth failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")