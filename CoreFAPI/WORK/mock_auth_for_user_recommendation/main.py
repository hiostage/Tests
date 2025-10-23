from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

MOCK_USERS = {
    "test_session": {
        "uuid": "d4fbe5146e",
        "firstName": "VLsAD",
        "lastName": "GAsB",
        "userName": "VGaberskorn",
        "email": "v.gaberskorn@mail.ru",
        "location": "Moscow",
        "skills": ["Python", "Django", "Docker"],
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    "another_session": {
        "uuid": "d407b8f468",
        "firstName": "VLAD",
        "lastName": "GAB",
        "userName": "VGberskorn",
        "email": "v.gabrskorn@mail.ru",
        "location": "Saint Petersburg",
        "skills": ["Go", "Docker"],
        "purpose_cooperation": "networking",
        "roles": ["backend"]
    },
    "extra_user_1": {
        "uuid": "d407b8f469",
        "firstName": "Alice",
        "lastName": "Smith",
        "userName": "alice123",
        "email": "alice@example.com",
        "location": "Moscow",
        "skills": ["Python", "Django"],
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    "extra_user_2": {
        "uuid": "d407b8f470",
        "firstName": "Bob",
        "lastName": "Johnson",
        "userName": "bob_dev",
        "email": "bob@example.com",
        "location": "New York",
        "skills": ["React", "Node.js"],
        "purpose_cooperation": "networking",
        "roles": ["frontend"]
    },
    "extra_user_3": {
        "uuid": "d407b8f4694",
        "firstName": "Alice3",
        "lastName": "Smith",
        "userName": "alice123",
        "email": "alice@example.com",
        "location": "Moscow",
        "skills": ["Python", "Django"],
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    "extra_user_5": {
        "uuid": "d407b8f46794",
        "firstName": "Alice2",
        "lastName": "Smith",
        "userName": "alice123",
        "email": "alice@example.com",
        "location": "Moscow",
        "skills": ["React", "Node.js"],
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    "extra_user_6": {
        "uuid": "d407b8gzf4694",
        "firstName": "Alice",
        "lastName": "Smith",
        "userName": "alice123",
        "email": "alice@example.com",
        "location": "Berlin",
        "skills": ["Python", "Django"],
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    "extra_user_7": {
        "uuid": "dz407b8gzf4694",
        "firstName": "Alice",
        "lastName": "Smith",
        "userName": "alice123",
        "email": "alice@example.com",
        "location": "Berlin",
        "skills": ["Python", "Django"],
        "purpose_cooperation": "networking",
        "roles": ["developer"]
    },
    "extra_user_4": {
        "uuid": "d407b8f4g70",
        "firstName": "Bob",
        "lastName": "Johnson",
        "userName": "bob_dev",
        "email": "bob@example.com",
        "location": "Berlin",
        "skills": ["React", "Node.js"],
        "purpose_cooperation": "networking",
        "roles": ["frontend"]
    }
}


@app.get("/user")
async def get_current_user(request: Request):
    session_id = request.cookies.get("sessionId")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session ID not provided")

    user = MOCK_USERS.get(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user

@app.post("/login")
async def login():
    # Просто заглушка
    return JSONResponse(
        content={"message": "Logged in (mock)"},
        headers={"Set-Cookie": "sessionId=test_session; Path=/;"}
    )

@app.post("/register")
async def register():
    return {"message": "Registered (mock)"}

@app.get("/check_session")
async def check_session(request: Request):
    session_id = request.cookies.get("sessionId")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session cookie not found")
    if session_id not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid session ID")
    return MOCK_USERS[session_id]

@app.get("/user/all")
async def get_all_users():
    return list(MOCK_USERS.values())

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mock_auth"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
