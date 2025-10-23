from itsdangerous import URLSafeSerializer

from fastapi import Request, Response

from app.utils.redis import redis

SECRET_KEY = "DASKDSADKDASK"

SESSION_COOKIE_NAME = "session_id"

serializes = URLSafeSerializer(SECRET_KEY)

async def create_session(response: Response, user_id: int):
    session_token = serializes.dumps({'user_id': user_id})
    await redis.set(f"session_id: {session_token}", user_id, ex=360)
    response.set_cookie(SESSION_COOKIE_NAME, session_token, httponly=True)
    

def get_user_id_from_session(request: Request) -> int | None:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)


    if not session_token:
        return None
    
    try:
        data = serializes.loads(session_token)
        return data.get('user_id')
    except Exception:
        return None
    
def logout_session(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)    