from fastapi import APIRouter
from api.v1.endpoints import users, projects, vacancies

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(vacancies.router, prefix="/vacancies", tags=["vacancies"])
