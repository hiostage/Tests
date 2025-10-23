from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import os
from typing import Dict, Any

app = FastAPI()

# Конфигурация из переменных окружения
VALID_TOKENS = os.getenv("AUTH_PROXY_TOKENS", "Bearer test-token").split(",")
REQUIRED_PERMISSIONS = {
    "groups.read": "Permission to read groups",
    "groups.write": "Permission to modify groups"
}

@app.get("/health")
async def health_check():
    """Эндпоинт для healthcheck"""
    return {"status": "healthy"}

@app.get("/auth/validate")
async def validate_token(request: Request):
    """Валидация токена и возврат пользовательских данных"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )
    
    if auth_header not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )
    
    # Возвращаем стандартный набор данных пользователя
    return {
        "sub": "mock-user-id-123",
        "username": "mock_user",
        "email": "mock_user@example.com",
        "permissions": list(REQUIRED_PERMISSIONS.keys()),
        "is_active": True,
        "token": auth_header  # для отладки
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Кастомный обработчик ошибок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": "auth_proxy_error",
            "status_code": exc.status_code
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)