from fastapi import APIRouter
from services.search import search

router = APIRouter()

@router.get("/")
async def search_projects(q: str):
    query = {"match": {"name": q}}
    return await search(index="projects", query=query)
