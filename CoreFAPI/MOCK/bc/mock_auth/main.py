from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Мок-данные пользователя
MOCK_USERS = {
    "test_session": {
        "user_id": 1,
        "username": "test_user",
        "permissions": ["groups.read", "groups.write"],
        "is_active": True
    }
}

@app.get("/check_session")
async def check_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid session")
    return MOCK_USERS[session_id]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}