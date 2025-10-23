from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api import groups, posts, users
from app.utils.rabbitmq import init_rabbitmq

app = FastAPI(title="Interest Groups Microservice", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])

@app.on_event("startup")
async def startup_event():
    await init_rabbitmq()

@app.get("/")
def read_root():
    return {"message": "Interest Groups Microservice is running"}