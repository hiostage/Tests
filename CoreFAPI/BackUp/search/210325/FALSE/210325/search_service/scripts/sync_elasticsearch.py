import asyncio
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.services.job_service import JobService

async def main():
    await UserService.sync_users()
    await ProjectService.sync_projects()
    await JobService.sync_jobs()

if __name__ == "__main__":
    asyncio.run(main())