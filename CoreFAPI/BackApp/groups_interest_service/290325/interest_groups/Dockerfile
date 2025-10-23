# Базовый образ (лучше использовать alpine для меньшего размера)
FROM python:3.9-alpine as builder

WORKDIR /app

# Устанавливаем зависимости, необходимые для сборки
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev postgresql-dev

# Копируем только зависимости для кэширования
COPY requirements.txt .

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.9-alpine

WORKDIR /app

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Устанавливаем рантайм-зависимости
RUN apk add --no-cache libpq

# Делаем sure что Python использует наше виртуальное окружение
ENV PATH="/opt/venv/bin:$PATH"

# Копируем код приложения
COPY . .

# Оптимизация для production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Меняем пользователя для безопасности
RUN adduser -D myuser && chown -R myuser:myuser /app
USER myuser

# Запускаем приложение (без --reload для production!)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]