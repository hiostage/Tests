from fastapi import FastAPI

from app.api import user

def create_app() -> FastAPI:
    app = FastAPI(
        title = 'User-TEST',
        docs_url = '/docs'
    )

    app.include_router(user.router)

    return app

app = create_app()