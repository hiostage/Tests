FROM python:3.12.6-alpine


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /news_feed

COPY pyproject.toml poetry.lock /news_feed/


RUN pip install poetry

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-directory


COPY ./alembic /news_feed/alembic
COPY alembic.ini /news_feed/
COPY ./app /news_feed/app

EXPOSE 8000

COPY entrypoint.sh /news_feed/entrypoint.sh
RUN chmod +x /news_feed/entrypoint.sh

ENTRYPOINT ["sh", "/news_feed/entrypoint.sh"]
