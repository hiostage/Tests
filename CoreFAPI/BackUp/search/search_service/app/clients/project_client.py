import httpx
from app.schemas.project import Project

class ProjectClient:
    @staticmethod
    async def get_projects():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://project-service:8000/projects")
            response.raise_for_status()
            return [Project(**project) for project in response.json()]