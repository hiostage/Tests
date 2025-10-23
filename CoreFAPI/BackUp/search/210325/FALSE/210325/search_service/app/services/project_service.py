from app.clients.project_client import ProjectClient
from app.db.elasticsearch import es
from app.schemas.project import ProjectSearchRequest
from fastapi import HTTPException
from app.db.redis import get_from_cache, set_to_cache, invalidate_cache

class ProjectService:
    @staticmethod
    async def search_projects(request: ProjectSearchRequest):
        # Создаем ключ для кэша на основе параметров запроса
        cache_key = f"search_projects:{request.query}:{request.technologies}"

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
            query["bool"]["must"].append({"match": {"name": request.query}})
        if request.technologies:
            query["bool"]["must"].append({"terms": {"technologies": request.technologies}})

        try:
            result = await es.search(index="projects", body={"query": query})
            hits = result["hits"]["hits"]

            # Сохраняем результат в кэше на 5 минут (300 секунд)
            set_to_cache(cache_key, hits, ttl=300)

            return hits
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_projects():
        projects = await ProjectClient.get_projects()
        for project in projects:
            await es.index(index="projects", id=project.id, body=project.dict())
        # Очищаем кэш для поиска проектов
        invalidate_cache("search_projects:*")