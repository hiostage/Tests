from fastapi import FastAPI

from app.api import calc

def start_up() -> FastAPI:
    app = FastAPI(
        title = "AHAH",
        docs_url = "/docs"
    )

    app.include_router(calc.router)

    return app


app = start_up()