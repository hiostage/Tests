from elasticsearch import AsyncElasticsearch
from app.core.config import settings

es = AsyncElasticsearch(settings.ELASTICSEARCH_URL)