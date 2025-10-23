from fastapi import HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, delete, asc, desc

from app.models.Users import User

from passlib.hash import bcrypt

from app.services.session_manager import create_session, get_user_id_from_session


from fastapi.encoders import jsonable_encoder
import json

from app.services.exeptions import UserNotAuthenticated, UserNotFound, UserInvalidPassword

NOT_FOUND = "_user_not_found_" 
NOT_AUTHENTICATED = "_user_not_authenticated_"
INVALID_PASSWORD = "_user_invalid_password_"


class UserLogic():
    def __init__(self, db: AsyncSession, redis):
        self.redis = redis
        self.db = db

    async def get_users(self):
        cache = await self.redis.get("get_all_users")
        if cache:
            return json.loads(cache)
        result = await self.db.execute(select(User).order_by(User.id.asc()))
        users = result.scalars().all()

        obj_json = json.dumps(jsonable_encoder(users)) 
        await self.redis.set("get_all_users", obj_json, ex=10)
        return users
    
    async def put_user(self, user_data, user_id):
        user = self._get_user_from_db(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        data = user_data.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user
    
    async def delete_all_users(self):
        await self.db.execute(delete(User))
        await self.db.commit()
        return {"status": "ok"}

    async def delete_user(self, user_id):
        user = self._get_user_from_db(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await self.db.delete(user)
        await self.db.commit()

        return {"status": f"{user.id} deleted."}
    
    async def login_user(self, user_data, session_id: int):
        stmt = select(User).filter(User.name == user_data.name)
        result = await self.db.execute(stmt)
        user = result.scalars().first()
        cache = await self.redis.get(f"correct_user: {session_id}")
        if cache:
            if cache == NOT_FOUND:
                raise UserNotFound()
            if cache == INVALID_PASSWORD:
                raise UserInvalidPassword()

        if not user:
            await self._cache_and_raise(session_id, NOT_FOUND, 5, UserNotFound)
        
        if not bcrypt.verify(user_data.password, user.password):
            await self._cache_and_raise(session_id, INVALID_PASSWORD, 5, UserInvalidPassword)
        
        return user
    

    async def get_correct_user(self, session_id: str):
        cache = await self.redis.get(f"correct_user: {session_id}")
        if cache:
            if cache == NOT_FOUND:
                raise UserNotFound()
            if cache == NOT_AUTHENTICATED:
                raise UserNotAuthenticated()
            return json.loads(cache)
        user_id = await self.redis.get(f"session_id: {session_id}")
        if not user_id:
            await self._cache_and_raise(session_id, NOT_AUTHENTICATED, 15, UserNotAuthenticated)
        
        user = await self._get_user_from_db(int(user_id))

        if not user:
            await self._cache_and_raise(session_id, NOT_FOUND, 15, UserNotFound)
            
        
        user_json = json.dumps(jsonable_encoder(user))

        await self.redis.set(f"correct_user: {session_id}", user_json, ex=10)

        return user
    
    async def _get_user_from_db(self, user_id: int):
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _cache_and_raise(self, session_id, value, ttl, exeption_cls):
        await self.redis.set(f"correct_user: {session_id}", value, ex=ttl)
        raise exeption_cls()
        
