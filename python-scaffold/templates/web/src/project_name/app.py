from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from {{project_name_snake}}.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="{{project_name}}",
        description="{{description}}",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app
