# Interest Groups Microservice

Микросервис для управления группами по интересам: создание групп, публикация постов, обсуждения, обмен опытом и участие в сообществах.

## 📦 Стек технологий

- Python 3.11  
- FastAPI  
- PostgreSQL  
- Redis  
- RabbitMQ  
- SQLAlchemy (async)  
- Alembic  
- Docker + Docker Compose  
- Pytest  

## 🚀 Функциональность

- Создание и управление группами по интересам  
- Присоединение и удаление из групп  
- Создание и удаление постов внутри групп  
- Уведомления о новых сообщениях (через RabbitMQ)  
- Подсчет участников 
- Поддержка вложенных моделей (автор поста и прочее)  

## 📁 Структура проекта

```
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
```

## 🧪 Запуск и тестирование

### Локальный запуск (Docker)

```bash
docker-compose up --build
```

Сервис будет доступен по адресу: [http://localhost:8000](http://localhost:8000)  
Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Запуск тестов

```bash
docker-compose run --rm tests
```

## 🔒 Аутентификация

Аутентификация реализована через отдельный сервис `mock_auth`, подключённый через переменную `AUTH_PROXY_URL`.  
В production заменяется на полноценный Auth-сервис.

## 📬 Взаимодействие с другими сервисами

- **Пользователи** — получаются из внешней базы данных  
- **Уведомления** — через RabbitMQ  
- **Кэширование** — Redis  

## 📌 Примеры API

### 🔹 `/groups`

| Метод   | Endpoint                                      | Описание               |
|---------|-----------------------------------------------|------------------------|
| POST    | `/api/v1/groups/`                             | Создать новую группу   |
| GET     | `/api/v1/groups/`                             | Получить список групп  |
| GET     | `/api/v1/groups/{group_id}`                   | Получить группу        |
| PUT     | `/api/v1/groups/{group_id}`                   | Обновить группу        |
| DELETE  | `/api/v1/groups/{group_id}`                   | Удалить группу         |
| POST    | `/api/v1/groups/{group_id}/members/{id}`      | Добавить участника     |
| DELETE  | `/api/v1/groups/{group_id}/members/{id}`      | Удалить участника      |

### 🔹 `/posts`

| Метод   | Endpoint                                         | Описание            |
|---------|--------------------------------------------------|---------------------|
| POST    | `/api/v1/posts/`                                 | Создать пост        |
| GET     | `/api/v1/posts/`                                 | Получить все посты  |
| GET     | `/api/v1/posts/group/{group_id}`                 | Посты группы        |
| PATCH   | `/api/v1/posts/{post_id}`                        | Обновить пост       |
| DELETE  | `/api/v1/posts/{post_id}`                        | Удалить пост        |

## 🗂️ Миграции базы данных

Для управления схемой БД используется **Alembic**.

Примеры команд:

```bash
alembic revision --autogenerate -m "Add new field to Group"
alembic upgrade head
```

## 📝 TODO
...


## Env файл

# ======== Базовые настройки ========
POSTGRES_HOST=db
REDIS_HOST=redis
RABBITMQ_HOST=rabbitmq

POSTGRES_PORT=5432
RABBITMQ_PORT=5672
REDIS_PORT=6379

# ======== Настройки БД ========
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=interest_groups
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# ======== Настройки Redis ========
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0

# ======== Настройки RabbitMQ ========
RABBITMQ_USER=user
RABBITMQ_PASS=password
RABBITMQ_VHOST=/
RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@${RABBITMQ_HOST}:${RABBITMQ_PORT}${RABBITMQ_VHOST}
RABBITMQ_TIMEOUT=10

# ======== Настройки для Auth Proxy ========
AUTH_PROXY_URL=http://mock_auth:8080  # URL для обращения к auth-proxy
# Для сервиса auth-proxy
REQUEST_TIMEOUT=5

# ======== CORS/Безопасность ========
ALLOWED_ORIGINS='["http://localhost:3000", "http://frontend.com"]'
CORS_ALLOW_CREDENTIALS=True
REQUIRE_SCOPES=True

# ======== Логирование ========
LOG_LEVEL=INFO
LOG_FORMAT=json

