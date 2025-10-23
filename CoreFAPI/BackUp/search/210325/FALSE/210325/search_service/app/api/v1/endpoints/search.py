from fastapi import APIRouter
from app.services.search_service import SearchService
from app.schemas.search import SearchRequest

router = APIRouter()

@router.post("/")
async def search(request: SearchRequest):
    return await SearchService.search(request)