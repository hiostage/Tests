from elasticsearch import AsyncElasticsearch

ELASTICSEARCH_URL = ["http://elasticsearch:9200"]  # Список хостов

INDEXES = {
    "users": {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "first_name": {"type": "text", "analyzer": "standard"},
                "last_name": {"type": "text", "analyzer": "standard"},
                "skills": {"type": "text", "analyzer": "standard"},
                "location": {"type": "text", "analyzer": "standard"},
                "company": {"type": "text", "analyzer": "standard"},
            }
        }
    },
    "projects": {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "standard"},
                "description": {"type": "text", "analyzer": "standard"},
                "technologies": {"type": "text", "analyzer": "standard"},
            }
        }
    },
    "vacancies": {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "standard"},
                "company": {"type": "text", "analyzer": "standard"},
                "skills": {"type": "text", "analyzer": "standard"},
                "location": {"type": "text", "analyzer": "standard"},
                "salary": {"type": "integer"},
            }
        }
    }
}

async def create_indexes():
    es = AsyncElasticsearch(ELASTICSEARCH_URL)
    
    for index_name, settings in INDEXES.items():
        exists = await es.indices.exists_index(index=index_name)  # Устаревший `exists` заменен на `exists_index`
        if not exists:
            await es.indices.create(index=index_name, mappings=settings["mappings"])  # Передаем mappings напрямую
            print(f"✅ Index '{index_name}' created.")
        else:
            print(f"⚠️ Index '{index_name}' already exists.")
    
    await es.close()
