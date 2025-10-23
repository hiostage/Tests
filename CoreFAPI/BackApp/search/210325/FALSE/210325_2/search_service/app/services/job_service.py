from app.clients.job_client import JobClient
from app.db.elasticsearch import es
from app.schemas.job import JobSearchRequest
from fastapi import HTTPException
from app.db.redis import get_from_cache, set_to_cache, invalidate_cache

class JobService:
    @staticmethod
    async def search_jobs(request: JobSearchRequest):
        # Создаем ключ для кэша на основе параметров запроса
        cache_key = f"search_jobs:{request.query}:{request.company}:{request.skills}:{request.location}:{request.min_salary}:{request.max_salary}"

        # Пытаемся получить данные из кэша
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return cached_data  # Если данные есть в кэше, возвращаем их

        # Если данных нет в кэше, выполняем поиск в Elasticsearch
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
            hits = result["hits"]["hits"]

            # Сохраняем результат в кэше на 5 минут (300 секунд)
            set_to_cache(cache_key, hits, ttl=300)

            return hits
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_jobs():
        jobs = await JobClient.get_jobs()
        for job in jobs:
            await es.index(index="jobs", id=job.id, body=job.dict())
        # Очищаем кэш для поиска вакансий
        invalidate_cache("search_jobs:*")