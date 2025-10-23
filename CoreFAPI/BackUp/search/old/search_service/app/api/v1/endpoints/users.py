from fastapi import APIRouter
from services.search import search

router = APIRouter()

@router.get("/")
async def search_users(q: str):
    query = {"match": {"first_name": q}}
    return await search(index="users", query=query)
