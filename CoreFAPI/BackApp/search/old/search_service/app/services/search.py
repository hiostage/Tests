from core.es_client import es

async def search(index: str, query: dict):
    response = await es.search(index=index, query=query)
    return response["hits"]["hits"]
