from app.clients.user_client import UserClient
from app.db.elasticsearch import es
from app.schemas.user import UserSearchRequest
from fastapi import HTTPException
from app.db.redis import get_from_cache, set_to_cache, invalidate_cache

class UserService:
    @staticmethod
    async def search_users(request: UserSearchRequest):
        # Создаем ключ для кэша на основе параметров запроса
        cache_key = f"search_users:{request.query}:{request.skills}:{request.location}"

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
        if request.skills:
            query["bool"]["must"].append({"terms": {"skills": request.skills}})
        if request.location:
            query["bool"]["must"].append({"match": {"location": request.location}})

        try:
            result = await es.search(index="users", body={"query": query})
            hits = result["hits"]["hits"]

            # Сохраняем результат в кэше на 5 минут (300 секунд)
            set_to_cache(cache_key, hits, ttl=300)

            return hits
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_users():
        users = await UserClient.get_users()
        for user in users:
            await es.index(index="users", id=user.id, body=user.dict())
        # Очищаем кэш для поиска пользователей
        invalidate_cache("search_users:*")