# python
User Recommendation Service

Микросервис рекомендаций пользователей на основе общих навыков, местоположения и цели сотрудничества. Используется в системе профессиональных знакомств/сети.

---

Возможности

- Получение персонализированных рекомендаций пользователей.
- Сортировка по приоритету: навыки, локация, роли.
- Пагинация и ограничение общего количества результатов.
- Подключение к внешнему сервису пользователей через сессию (MOCK) (`sessionId`).

---

Стек технологий

- Python 3.11+
- FastAPI
- asyncio
- HTTPX (в ExternalUserClient)
- Docker

---

Структура проекта

user_recommendation/
├── app/
│   ├── clients/
│   │   ├── user_client.py
│   ├── db/
│   │   ├── migrations/
│   │   └── databse.py
│   ├── main.py
│   ├── models.py
│   ├── repositories.py
│   ├── routers.py
├── alembic.ini
├── pyproject.toml
└── README.md



---

Пример запроса

GET /recommendations

Пример JSON тела:

{
  "purpose_cooperation": "job_search",
  "priority": "skills",
  "page_limit": 10,
  "total_limit": 100,
  "page": 1
}

> Требуется передать cookie: sessionId

---

Логика ранжирования

Функция calculate_relevance_score() определяет релевантность пользователя:

| Критерий        | priority = skills     | priority = location   | default         |
|-----------------|-----------------------|------------------------|-----------------|
| Совпадение skills     | 5 баллов за каждый     | 3 балла за каждый       | 2 балла         |
| Совпадение локации    | 2 балла                | 5 баллов                | 3 балла         |
| Совпадение ролей      | 0.3 балла за каждую    | 0.3 балла за каждую     | 0.3 балла       |

---

Тестирование

Пока что нет

---

Пример мок-данных

MOCK_USERS = {
    "test_session": {
        "uuid": "d4fbe5146e",
        "skills": ["Python", "Django", "Docker"],
        "location": "Moscow",
        "purpose_cooperation": "job_search",
        "roles": ["developer"]
    },
    ...
}

---
