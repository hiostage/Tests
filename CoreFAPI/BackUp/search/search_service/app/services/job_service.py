from app.clients.job_client import JobClient
from app.db.elasticsearch import es
from app.schemas.job import JobSearchRequest
from fastapi import HTTPException

class JobService:
    @staticmethod
    async def search_jobs(request: JobSearchRequest):
        query = {
            "bool": {
                "must": []
            }
        }
        if request.query:
            query["bool"]["must"].append({"match": {"title": request.query}})
        if request.company:
            query["bool"]["must"].append({"match": {"company": request.company}})
        if request.skills:
            query["bool"]["must"].append({"terms": {"skills": request.skills}})
        if request.location:
            query["bool"]["must"].append({"match": {"location": request.location}})
        if request.min_salary is not None or request.max_salary is not None:
            salary_range = {}
            if request.min_salary is not None:
                salary_range["gte"] = request.min_salary
            if request.max_salary is not None:
                salary_range["lte"] = request.max_salary
            query["bool"]["must"].append({"range": {"salary": salary_range}})

        try:
            result = await es.search(index="jobs", body={"query": query})
            return result["hits"]["hits"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_jobs():
        jobs = await JobClient.get_jobs()
        for job in jobs:
            await es.index(index="jobs", id=job.id, body=job.dict())