from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.depends import get_authenticated_user, get_user_service
from app.api.models.user import ActivateUserRequest, UserCreate, UserResponse
from app.db.user import UniqueViolationError, User
from app.services.user import (
    CodeExpiredError,
    CodeInvalidError,
    CodeNotFoundError,
    UserService,
)

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


@router.post(
    "/users/activate",
    status_code=status.HTTP_200_OK,
)
async def activate_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    authenticated_user: Annotated[User, Depends(get_authenticated_user)],
    activate_request: ActivateUserRequest,
) -> Response:
    try:
        await user_service.activate_user(authenticated_user, activate_request.code)
        return Response(
            content="User activated successfully", status_code=status.HTTP_200_OK
        )
    except (CodeExpiredError, CodeInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Activation failed: {e.message}",
        )
    except CodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activation failed: {e.message}",
        )
