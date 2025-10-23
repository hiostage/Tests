from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

MOCK_USERS = {
    "test_session": {  # Используем тот же ключ, что и в рабочей версии
        "uuid": "d4fbe5146e",
        "firstName": "VLsAD",
        "lastName": "GAsB",
        "userName": "VGaberskorn",
        "email": "v.gaberskorn@mail.ru",
        "phone": None,
        "roles": None
    },
    "another_session": {
        "uuid": "d407b8f468",
        "firstName": "VLAD",
        "lastName": "GAB",
        "userName": "VGberskorn",
        "email": "v.gabrskorn@mail.ru",
        "phone": None,
        "roles": None
    },
}

@app.get("/check_session")
async def check_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Session cookie not found",
            headers={"WWW-Authenticate": "Cookie"}
        )
    if session_id not in MOCK_USERS:
        raise HTTPException(
            status_code=401,
            detail="Invalid session ID",
            headers={"WWW-Authenticate": "Cookie"}
        )
    return MOCK_USERS[session_id]

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mock_auth"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)