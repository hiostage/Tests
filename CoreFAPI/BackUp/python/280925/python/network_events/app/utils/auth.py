from fastapi import Request, HTTPException
import httpx
from app.core.config import settings
from app.schemas.user import UserPublic

async def get_current_user(request: Request):
    session_id = request.cookies.get("sessionId")
    print("sadpaskd", settings.AUTH_PROXY_URL)
    if not session_id:
        raise HTTPException(status_code=401, detail="No session_id cookie found")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.AUTH_PROXY_URL}user", cookies={"sessionId": session_id})
        if response.status_code == 200:
            return UserPublic(**response.json())
        raise HTTPException(status_code=401, detail="Unauthorized")
