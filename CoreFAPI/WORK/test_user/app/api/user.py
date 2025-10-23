from fastapi import APIRouter, Depends, Request, Response, HTTPException

from app.scheme.scheme import UserScheme, UserSchemeID, UserSchemeForUpdate, UserLoginSchema, ValueId, ValueResult
from app.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Users import User

from sqlalchemy import select

from app.services.user_logic import UserLogic

from passlib.hash import bcrypt

from app.services.session_manager import logout_session

from app.services.httpx import get_val_from_service

import json

from app.utils.redis import get_redis

from app.services.exeptions import UserNotAuthenticated, UserNotFound, UserInvalidPassword

from app.services.session_manager import create_session

router = APIRouter()

SESSION_ID = "session_id"

@router.post('/add-user')
async def add_user(user_data:UserScheme, db: AsyncSession = Depends(get_db)):
    hashed_password = bcrypt.hash(user_data.password)
    db.add(User(name = user_data.name, email = user_data.email, phone = user_data.phone, password = hashed_password))
    await db.commit()
    return user_data

@router.get('/get-user')
async def get_user(db: AsyncSession = Depends(get_db)):
    logic = UserLogic(db)
    return await logic.get_users()

@router.put('/put-user/{event_id}')
async def put_user(user_id: int, user_data: UserSchemeForUpdate, db: AsyncSession = Depends(get_db)):
    logic = UserLogic(db)
    return await logic.put_user(user_data, user_id)

@router.delete('/delete-all-users')
async def delete_all_users(db: AsyncSession = Depends(get_db)):
    logic = UserLogic(db)

    return await logic.delete_all_users()


@router.delete('/delete-user/{event_id}')
async def delete_user(user_id:int, db: AsyncSession = Depends(get_db)):
    logic = UserLogic(db)
    return await logic.delete_user(user_id)

@router.post('/login')
async def login_user(response: Response, 
                     user_data: UserLoginSchema, 
                     db: AsyncSession = Depends(get_db), 
                     redis = Depends(get_redis)):
    
    logic = UserLogic(db, redis)
    try:
        user = await logic.login_user(user_data, response)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User Not Found")
    except UserInvalidPassword:
        raise HTTPException(status_code=401, detail="Invalid Password")
    
    await create_session(response, user.id)

    return {"message":"Login success", "user_data": {"id":user.id, "name":user.name}}


@router.get('/get-correct-user')
async def get_user(request: Request, db: AsyncSession = Depends(get_db), redis = Depends(get_redis)):
    session_id = request.cookies.get(SESSION_ID)
    user_services = UserLogic(db, redis)
    try:
        user = await user_services.get_correct_user(session_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User Not Found")
    except UserNotAuthenticated:
        raise HTTPException(status_code=401, detail="Not Authenticated")
    return user

@router.post('/logout')
async def logout(response: Response):
    return logout_session(response)

@router.post('/add-value/{user_id}')
async def add_value(event: ValueId, user_id: int, db: AsyncSession = Depends(get_db)):
    stmt= select(User).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    val = await get_val_from_service(val_id=event.value_id)

    user.value_result = json.dumps(val)

    await db.commit()

    return val


    