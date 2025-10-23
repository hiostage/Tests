from fastapi import FastAPI
from app.api import api


def start_up() -> FastAPI:
    app = FastAPI(
        docs_url='/docs',
        title = 'Adpoaspodjkasop'
    )

    app.include_router(api.router)

    return app


app = start_up()