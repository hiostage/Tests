# Interest Groups Microservice

Микросервис для управления группами по интересам: создание групп, публикация постов, обсуждения, обмен опытом и участием в сообществах.

## 📦 Стек технологий

- Python 3.11
- FastAPI
- PostgreSQL
- Redis
- RabbitMQ
- SQLAlchemy (async)
- Docker + Docker Compose
- Pytest

## 🚀 Функциональность

- Создание и управление группами по интересам
- Присоединение и выход из групп
- Создание и удаление постов внутри групп
- Уведомления о новых сообщениях (через RabbitMQ)
- Подсчет участников и комментариев
- Поддержка вложенных моделей (автор поста и прочее)

## 📁 Структура проекта

interest_groups/ 
├── .env
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── init-db.sql
├── requirements.txt
├── alembic.ini
├── logs/
├── migrations/
├── tests/
│
├── app/               
│   ├── __init__.py
│   ├── main.py 
│   ├── models/            
│   │   ├── base.py 
│   │   ├── group.py  
│   │   ├── post.py  
│   │   ├── user.py     
│   │   └── __init__.py  
│   │
│   ├── schemas/          
│   │   ├── group.py   
│   │   ├── post.py   
│   │   ├── user.py  
│   │   └── __init__.py  
│   │
│   ├── core/             
│   │   ├── config.py  
│   │   └── __init__.py  
│   │
│   ├── db/                
│   │   ├── redis.py        
│   │   ├── session.py      
│   │   └── __init__.py  
│   │
│   ├── api/            
│   │   ├── routers/  
│   │   ├── groups.py   
│   │   ├── posts.py   
│   │   └── __init__.py   
│   │
│   ├── services/         
│   │   ├── group.py 
│   │   ├── post.py       
│   │   ├── user.py        
│   │   └── __init__.py  
│   │
│   └── utils/          
│       ├── auth.py
│       ├── cache.py
│       ├── logger.py
│       ├── rabbitmq.py
│       └── __init__.py


## Запуск
### Локально (с Docker)

```bash
docker-compose up --build

Сервис будет доступен по адресу: http://localhost:8000

Swagger UI: http://localhost:8000/docs


Тесты

docker-compose run --rm tests


🔒 Аутентификация
Аутентификация реализована через отдельный сервис mock_auth, подключённый через переменную AUTH_PROXY_URL.
В production заменяется на настоящий Auth-сервис.

📬 Взаимодействие с другими сервисами
Получение информации о пользователях — из внешней базы данных

Уведомления — через RabbitMQ

Кэширование — Redis

📌 Примеры API
/groups

Метод	Endpoint	Описание
POST	/api/v1/groups/	Создать новую группу
GET	/api/v1/groups/	Получить список групп
GET	/api/v1/groups/{group_id}	Получить конкретную группу
PUT	/api/v1/groups/{group_id}	Обновить группу
DELETE	/api/v1/groups/{group_id}	Удалить группу
POST	/api/v1/groups/{group_id}/members/{id}	Добавить участника
DELETE	/api/v1/groups/{group_id}/members/{id}	Удалить участника
/posts

Метод	Endpoint	Описание
POST	/api/v1/posts/	Создать пост
GET	/api/v1/posts/	Получить все посты
GET	/api/v1/posts/group/{group_id}	Получить посты группы
PATCH	/api/v1/posts/{post_id}	Обновить пост
DELETE	/api/v1/posts/{post_id}	Удалить пост

📝 TODO
Документация по очередям RabbitMQ


#Env файл

# ======== Базовые настройки ========
POSTGRES_HOST=db
REDIS_HOST=redis
RABBITMQ_HOST=rabbitmq

POSTGRES_PORT=5432
RABBITMQ_PORT=5672
REDIS_PORT=6379

# ======== Версии сервисов ========
POSTGRES_VERSION=15-alpine
REDIS_VERSION=7-alpine
RABBITMQ_VERSION=3.12-management

# ======== Настройки БД ========
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=interest_groups
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_CONNECT_TIMEOUT=5

# ======== Настройки Redis ========
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
REDIS_CACHE_TTL=300
REDIS_TIMEOUT=3

# ======== Настройки RabbitMQ ========
RABBITMQ_USER=user
RABBITMQ_PASS=password
RABBITMQ_VHOST=/
RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@${RABBITMQ_HOST}:${RABBITMQ_PORT}${RABBITMQ_VHOST}
RABBITMQ_TIMEOUT=10

# ======== Настройки для Auth Proxy ========
AUTH_PROXY_URL=http://mock_auth:8080  # URL для обращения к auth-proxy
# Для сервиса auth-proxy
AUTH_PROXY_TOKEN=your_service_token  # Основной токен
AUTH_PROXY_FALLBACK_TOKEN=test-token  # Дополнительный токен (опционально)
REQUEST_TIMEOUT=5
# Для других сервисов, обращающихся к auth-proxy
AUTH_PROXY_INTERNAL_URL=http://auth-proxy:8080  # Для обращения между контейнерами
AUTH_PROXY_EXTERNAL_URL=http://localhost:8080  # Для доступа с хоста

# ======== CORS/Безопасность ========
ALLOWED_ORIGINS='["http://localhost:3000", "http://frontend.com"]'
CORS_ALLOW_CREDENTIALS=True
REQUIRE_SCOPES=True

# ======== Логирование ========
LOG_LEVEL=INFO
LOG_FORMAT=json

