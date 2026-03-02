from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status

from app.api.models.common import StatusResponse
from app.api.routes.user import router as user_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.db.pool import pool
from app.services.resend_client import resend_client

configure_logging()

_tags_metadata = [
    {
        "name": "Users",
        "description": "User registration and email-based account activation.",
    },
    {
        "name": "Health",
        "description": "Service liveness probe.",
    },
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up")
    async with pool(), resend_client():
        yield
    logger.info("Shut down")


app = FastAPI(
    title="User Registration API",
    version="1.0.0",
    description=(
        "REST API for user registration and email-based account activation. "
        "New accounts are created inactive and require a 4-digit verification "
        "code (sent by email) to become active."
    ),
    openapi_tags=_tags_metadata,
    lifespan=lifespan,
)
app.include_router(user_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"{request.method} {request.url}")
    safe_headers = {
        k: v for k, v in request.headers.items() if k.lower() != "authorization"
    }
    logger.debug(f"Headers: {safe_headers}")
    response = await call_next(request)
    logger.debug(f"Completed with status {response.status_code}")
    return response


@app.get(
    "/status",
    status_code=status.HTTP_200_OK,
    response_model=StatusResponse,
    tags=["Health"],
    summary="Health check",
    description='Returns `{"status": "ok"}` when the service is running.',
)
async def status_check() -> StatusResponse:
    return StatusResponse(status="ok")
