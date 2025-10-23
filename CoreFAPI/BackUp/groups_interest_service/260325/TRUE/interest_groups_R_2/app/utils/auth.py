from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, Union, Dict, Any
import logging
import os
import httpx  # Используем асинхронный HTTP-клиент
from datetime import timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Mock config
MOCK_AUTH = os.getenv("MOCK_AUTH", "False").lower() == "true"
DEFAULT_USER_ID = int(os.getenv("DEFAULT_USER_ID", "1"))

# External user service config
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
USER_SERVICE_TIMEOUT = int(os.getenv("USER_SERVICE_TIMEOUT", "5"))

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scheme_name="JWT",
    auto_error=False
)

class UserModel(BaseModel):
    id: int
    username: str
    email: Optional[str] = None

async def fetch_user_from_external_service(token: str) -> UserModel:
    """Запрашивает данные пользователя из внешнего сервиса."""
    async with httpx.AsyncClient(timeout=USER_SERVICE_TIMEOUT) as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return UserModel(**response.json())
        except httpx.RequestError as e:
            logger.error(f"User service connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service unavailable"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"User service returned error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    request: Request = None
) -> UserModel:
    if MOCK_AUTH:
        logger.warning("Using mock authentication")
        return UserModel(id=DEFAULT_USER_ID, username="mock_user")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        # Валидация токена (если требуется)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Запрос к внешнему сервису
        return await fetch_user_from_external_service(token)
    
    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")