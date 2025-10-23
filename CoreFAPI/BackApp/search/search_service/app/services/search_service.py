from app.db.elasticsearch import es
from app.schemas.search import SearchRequest
from fastapi import HTTPException

class SearchService:
    @staticmethod
    async def search(request: SearchRequest):
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

        sort = []
        if request.sort_by:
            sort_order = request.sort_order if request.sort_order else "asc"
            sort.append({request.sort_by: {"order": sort_order}})

        try:
            result = await es.search(
                index=["users", "projects", "jobs"],
                body={
                    "query": query,
                    "sort": sort
                }
            )
            return result["hits"]["hits"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))