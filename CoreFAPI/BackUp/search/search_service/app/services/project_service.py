from app.clients.project_client import ProjectClient
from app.db.elasticsearch import es
from app.schemas.project import ProjectSearchRequest
from fastapi import HTTPException

class ProjectService:
    @staticmethod
    async def search_projects(request: ProjectSearchRequest):
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
            return result["hits"]["hits"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def sync_projects():
        projects = await ProjectClient.get_projects()
        for project in projects:
            await es.index(index="projects", id=project.id, body=project.dict())