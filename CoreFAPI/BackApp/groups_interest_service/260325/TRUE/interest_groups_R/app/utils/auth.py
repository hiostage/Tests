from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, Union, Dict, Any
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Mock config - set MOCK_AUTH=True in environment to bypass auth
MOCK_AUTH = os.getenv("MOCK_AUTH", "False").lower() == "true"
DEFAULT_USER_ID = int(os.getenv("DEFAULT_USER_ID", "1"))

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scheme_name="JWT",
    auto_error=False  # Allows optional auth for testing
)

class TokenData(BaseModel):
    username: Optional[str] = None
    id: Optional[int] = None

class UserModel(BaseModel):
    id: int
    username: str
    email: Optional[str] = None

# Security config (should be in environment variables in production)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    request: Request = None
) -> UserModel:
    """
    Get current user from JWT token or return mock user if auth is disabled.
    Returns UserModel (Pydantic model) for consistent interface.
    """
    # Bypass auth for testing
    if MOCK_AUTH:
        logger.warning("Authentication mock is active! Using default user")
        return UserModel(id=DEFAULT_USER_ID, username="mock_user")
    
    if not token:
        logger.error("No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            logger.error("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
            
        token_data = TokenData(id=user_id)
        
    except JWTError as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production, you would fetch user from another service here
    return UserModel(id=token_data.id, username=f"user{token_data.id}")

async def get_admin_user(current_user: UserModel = Depends(get_current_user)):
    """Example of role-based dependency"""
    if current_user.id != 1:  # Now using .id access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user