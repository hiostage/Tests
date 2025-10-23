from fastapi import FastAPI
from app.api import test 


def app_setup() -> FastAPI:
    app = FastAPI(
        title="TEST",
        docs_url="/docs",
        redoc_url="/redocs",
        openapi_url="/openapi.json",
    )


    app.include_router(test.router)

    return app


app = app_setup()
