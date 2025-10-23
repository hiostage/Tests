from fastapi import FastAPI
from app.routers import router


app = FastAPI(
    title="Recommendations API",
)

app.include_router(router, prefix="/recommendations")
