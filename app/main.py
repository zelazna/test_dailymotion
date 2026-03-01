from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status

from app.api.routes.user import router as user_router
from app.core.config import settings
from app.core.pool import pool


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    async with pool():
        yield


app = FastAPI(title="User Registration API", version="1.0.0", lifespan=lifespan)
app.include_router(user_router, prefix=settings.API_V1_STR)


@app.get(
    "/status",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def status_check() -> dict:
    return {"status": "ok"}
