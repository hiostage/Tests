from fastapi import FastAPI
from app.api import events, participants
from app.db.database import create_db_and_tables

def create_app() -> FastAPI:
    app = FastAPI(
        title="Сетевые мероприятия",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Подключаем роутеры
    app.include_router(participants.router)
    app.include_router(events.router)
    
    return app

app = create_app()

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
