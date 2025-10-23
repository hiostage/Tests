from fastapi import FastAPI
from app.api.routers import groups, posts, comments
from app.config.settings import settings

app = FastAPI(title="Groups Interest Service")

app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}