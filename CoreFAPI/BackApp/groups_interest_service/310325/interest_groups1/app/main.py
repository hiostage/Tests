from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api import groups, posts, users
from app.utils.rabbitmq import RabbitMQManager, init_rabbitmq
from app.utils.logger import logger
import os
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Starting application initialization...")
    
    try:
        await check_db_connection()
        await initialize_rabbitmq()
        logger.info("Application startup completed")
    except Exception as e:
        logger.critical(f"Application startup failed: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down application...")

app = FastAPI(
    title="Interest Groups Microservice",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])

async def initialize_rabbitmq():
    """Инициализация подключения к RabbitMQ"""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            await init_rabbitmq()
            logger.info("RabbitMQ connection established")
            return
        except Exception as e:
            logger.warning(f"RabbitMQ connection failed (attempt {attempt}/{max_retries}): {str(e)}")
            if attempt == max_retries:
                logger.error("Failed to connect to RabbitMQ after all retries")
                raise
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 10)

async def check_db_connection():
    """Проверка подключения к БД"""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("Database connection established")
            return
        except Exception as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error("Failed to connect to database after all retries")
                raise
            await asyncio.sleep(retry_delay)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        rabbitmq_status = "up" if hasattr(RabbitMQManager, "_connection") and RabbitMQManager._connection else "down"
        
        return {
            "status": "healthy",
            "services": {
                "database": "up",
                "rabbitmq": rabbitmq_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unavailable")

@app.get("/")
async def read_root():
    """Root endpoint"""
    return {"message": "Interest Groups Microservice is running"}