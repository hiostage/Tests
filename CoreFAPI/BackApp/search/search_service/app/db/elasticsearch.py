from elasticsearch import AsyncElasticsearch

# Создаём клиент Elasticsearch с указанием заголовков
es = AsyncElasticsearch(
    "http://elasticsearch:9200",  # URL вашего Elasticsearch
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
)