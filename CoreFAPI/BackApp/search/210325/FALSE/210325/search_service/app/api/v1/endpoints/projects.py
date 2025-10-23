from fastapi import APIRouter
from app.services.project_service import ProjectService
from app.schemas.project import ProjectSearchRequest

router = APIRouter()

@router.post("/search")
async def search_projects(request: ProjectSearchRequest):
    return await ProjectService.search_projects(request)