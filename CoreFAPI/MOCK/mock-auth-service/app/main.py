import os
import json
import time
import logging
from pathlib import Path
from typing import List
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
def get_allowed_origins() -> List[str]:
    origins = os.getenv("ALLOWED_ORIGINS", "[]")
    try:
        return json.loads(origins.replace("'", '"'))
    except json.JSONDecodeError:
        logger.warning("Failed to parse ALLOWED_ORIGINS, using default ['*']")
        return ["*"]

# Загрузка ключей
def load_keys():
    try:
        private_key = Path("/app/private.pem").read_text()
        public_key = Path("/app/public.pem").read_text()
        return private_key, public_key
    except Exception as e:
        logger.error(f"Key loading failed: {str(e)}")
        raise RuntimeError("Failed to load JWT keys")

# Инициализация
private_key, public_key = load_keys()
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    user_id: int
    username: str

# Валидация сервисного токена
def verify_service_token(x_service_token: str = Header(...)):
    expected_token = os.getenv("AUTH_SERVICE_TOKEN")
    if not expected_token:
        logger.error("AUTH_SERVICE_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Service misconfigured")
    
    if x_service_token != expected_token:
        logger.warning(f"Invalid service token received: {x_service_token}")
        raise HTTPException(status_code=403, detail="Invalid service token")

# Генерация JWT
def create_jwt(username: str) -> str:
    payload = {
        "sub": username,
        "user_id": 1,  # Mock user ID
        "exp": time.time() + 3600  # Expires in 1 hour
    }
    try:
        return jwt.encode(payload, private_key, algorithm="RS256")
    except Exception as e:
        logger.error(f"JWT generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token generation error")

# Эндпоинты
@app.post(os.getenv("AUTH_TOKEN_URL", "/auth/token"))
async def login(
    auth_data: TokenRequest,
    x_service_token: str = Depends(verify_service_token)
):
    logger.info(f"Login attempt for user: {auth_data.username}")
    
    if auth_data.username == "admin" and auth_data.password == "admin":
        return TokenResponse(access_token=create_jwt(auth_data.username))
    
    logger.warning(f"Failed login attempt for user: {auth_data.username}")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/v1/auth/verify")
async def verify_token(
    token: str,
    x_service_token: str = Depends(verify_service_token)
):
    try:
        logger.info(f"Verification attempt for token: {token[:50]}...")
        
        # Добавьте эту проверку
        if not token:
            raise HTTPException(status_code=400, detail="Empty token provided")
            
        # Декодирование с подробным логированием
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
            logger.info(f"Successful verification for user: {payload.get('sub')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during verification")
    
@app.get("/check_keys")
async def check_keys():
    try:
        test_payload = {"test": "value", "sub": "tester"}
        test_token = jwt.encode(test_payload, private_key, algorithm="RS256")
        decoded = jwt.decode(test_token, public_key, algorithms=["RS256"])
        return {
            "keys_valid": decoded == test_payload,
            "public_key": public_key[:50] + "..." if public_key else "MISSING",
            "private_key": "PRESENT" if private_key else "MISSING"
        }
    except Exception as e:
        return {"error": str(e)}