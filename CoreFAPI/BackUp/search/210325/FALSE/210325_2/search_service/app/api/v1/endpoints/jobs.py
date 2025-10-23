from fastapi import APIRouter
from app.services.job_service import JobService
from app.schemas.job import JobSearchRequest

router = APIRouter()

@router.post("/search")
async def search_jobs(request: JobSearchRequest):
    return await JobService.search_jobs(request)