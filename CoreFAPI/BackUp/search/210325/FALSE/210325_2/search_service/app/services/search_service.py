from app.db.elasticsearch import es
from app.schemas.search import SearchRequest
from fastapi import HTTPException
from app.db.redis import get_from_cache, set_to_cache

class SearchService:
    @staticmethod
    async def search(request: SearchRequest):
        # Создаем ключ для кэша на основе параметров запроса
        cache_key = f"search:{request.query}:{request.filters}"

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
            query["bool"]["must"].append({"multi_match": {"query": request.query}})
        if request.filters:
            for key, value in request.filters.items():
                query["bool"]["must"].append({"match": {key: value}})

        try:
            result = await es.search(
                index=["users", "projects", "jobs"],
                body={"query": query}
            )
            hits = result["hits"]["hits"]

            # Сохраняем результат в кэше на 5 минут (300 секунд)
            set_to_cache(cache_key, hits, ttl=300)

            return hits
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))