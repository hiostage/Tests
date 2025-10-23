from fastapi import Request, HTTPException
import httpx
import os

AUTH_PROXY_URL = os.getenv("AUTH_PROXY_URL", "http://localhost:8080")

async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session_id cookie found")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_PROXY_URL}/user", json={"session_id": session_id})
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=401, detail="Unauthorized")
