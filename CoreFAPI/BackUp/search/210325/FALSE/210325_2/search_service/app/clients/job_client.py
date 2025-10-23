import httpx
from app.schemas.job import Job

class JobClient:
    @staticmethod
    async def get_jobs():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://job-service:8000/jobs")
            response.raise_for_status()
            return [Job(**job) for job in response.json()]