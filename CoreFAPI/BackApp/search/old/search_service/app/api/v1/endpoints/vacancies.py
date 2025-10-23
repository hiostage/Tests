from fastapi import APIRouter
from services.search import search

router = APIRouter()

@router.get("/")
async def search_vacancies(q: str):
    query = {"match": {"title": q}}
    return await search(index="vacancies", query=query)
