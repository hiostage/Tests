from fastapi import APIRouter
from app.services.user_service import UserService
from app.schemas.user import UserSearchRequest

router = APIRouter()

@router.post("/search")
async def search_users(request: UserSearchRequest):
    return await UserService.search_users(request)