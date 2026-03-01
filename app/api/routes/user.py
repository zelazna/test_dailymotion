from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.depends import get_user_service
from app.api.models.user import UserCreate, UserResponse
from app.db.user import UniqueViolationError
from app.services.user import UserService

router = APIRouter()


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    body: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        user = await user_service.create_user(body.email, body.password)
    except UniqueViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)
