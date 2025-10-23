from elasticsearch import AsyncElasticsearch

es = AsyncElasticsearch("http://elasticsearch:9200")

async def save_to_elasticsearch(index, doc_id, body):
    await es.index(index=index, id=doc_id, document=body)
