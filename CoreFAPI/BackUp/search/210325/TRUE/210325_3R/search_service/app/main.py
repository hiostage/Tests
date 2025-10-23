from fastapi import FastAPI
from app.api.v1.endpoints import users, projects, jobs, search

app = FastAPI(title="Search Service")

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])