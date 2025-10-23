from app.clients.user_client import UserClient
from app.db.elasticsearch import es
from app.schemas.user import UserSearchRequest
from fastapi import HTTPException

class UserService:
    @staticmethod
    async def search_users(request: UserSearchRequest):
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
            return result["hits"]["hits"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_users():
        users = await UserClient.get_users()
        for user in users:
            await es.index(index="users", id=user.id, body=user.dict())