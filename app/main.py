from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status

from app.api.routes.user import router as user_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.db.pool import pool
from app.services.resend_client import resend_client

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up")
    async with pool(), resend_client():
        yield
    logger.info("Shut down")


app = FastAPI(title="User Registration API", version="1.0.0", lifespan=lifespan)
app.include_router(user_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"{request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.debug(f"Completed with status {response.status_code}")
    return response


@app.get(
    "/status",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def status_check() -> dict:
    return {"status": "ok"}
