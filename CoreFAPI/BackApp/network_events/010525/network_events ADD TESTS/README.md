# Сетевые мероприятия

Сервис для организации и управления сетевыми мероприятиями (онлайн и оффлайн), регистрации участников, обмена контактами и отправки уведомлений. Сервис использует **FastAPI**, **RabbitMQ** для асинхронной коммуникации, **Redis** для кеширования и **PostgreSQL** для хранения данных.

## 📁 Структура проекта

```
app/
├── api/            # Маршруты API для обработки запросов
├── db/             # Логика работы с базой данных (PostgreSQL)
├── services/       # Сервисы для бизнес-логики
├── schemas/        # Pydantic-схемы для валидации данных
├── utils/          # Вспомогательные функции, включая интеграцию с RabbitMQ
docker/             # Docker-контейнеры для развертывания приложения и зависимостей
```

## 🚀 Установка

2. Убедитесь, что у вас установлены **Docker** и **Docker Compose**.

3. Запустите сервис с помощью Docker Compose:

```bash
docker-compose up --build
```

## ⚙️ Развертывание

Контейнеры, необходимые для запуска:

- **app**: FastAPI приложение.
- **mock_auth**: мок-сервис авторизации.
- **db**: PostgreSQL база данных.
- **redis**: Redis.
- **rabbitmq**: RabbitMQ брокер сообщений.

## 🛠 Настройка среды

Создайте файл `.env` и добавьте в него следующие переменные:

```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/events_db
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//

# ======== Настройки для Auth Proxy ========
AUTH_PROXY_URL=http://mock_auth:8080  # URL для обращения к auth-proxy
# Для сервиса auth-proxy
REQUEST_TIMEOUT=5

```

## 📌 Основные маршруты API

- `POST /events/` — создание сетевого события.

```json
{
  "title": "Сетевое мероприятие 2025",
  "description": "Мероприятие для общения и нетворкинга.",
  "location": "Ru"
}
```

- `GET /events/{event_id}` — получение события по ID.
- `GET /events/` — список всех событий.
- `DELETE /events/{event_id}` — удаление события.
- `POST /register` — регистрация пользователя на событие. Требует куку session_id, например: session_id=test_session
- `GET /event/{event_id}/participant` — Получение списка участников.
- `DELETE /event/{event_id}/participant` — Отписка от события.

## 🔔 Интеграция с RabbitMQ

- При создании события публикуется сообщение в очередь `event_creation`.
- При регистрации/удалении с события — в очередь `event_participants`.

## ✅ Тестирование
- Тесты написаны на pytest с использованием httpx.AsyncClient и моков.

```bash
docker exec -it <'app_name'> pytest
```
- Покрытие:
    Создание событий
    Регистрация и удаление участников
    Получение списка участников
- Важно: Для тестов используется мок-авторизация (mock_auth). Убедитесь, что при тестировании передаётся кука session_id=test_session.

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📊 Логирование и мониторинг

- RabbitMQ Management: [http://localhost:15672](http://localhost:15672)
- Логин/пароль: `guest / guest`
