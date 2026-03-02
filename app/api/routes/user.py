from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.depends import get_authenticated_user, get_user_service
from app.api.models.common import ErrorDetail
from app.api.models.user import ActivateUserRequest, UserCreate, UserResponse
from app.db.user import UniqueViolationError, User
from app.services.user import (
    CodeExpiredError,
    CodeInvalidError,
    CodeNotFoundError,
    UserService,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Register a new user",
    description=(
        "Creates an inactive user account and sends a 4-digit numeric verification "
        "code to the provided email address. Use `POST /users/activate` to complete "
        "registration."
    ),
    responses={
        409: {
            "model": ErrorDetail,
            "description": "Email address is already registered.",
        },
    },
)
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
    "/activate",
    status_code=status.HTTP_200_OK,
    summary="Activate user account",
    description=(
        "Validates the 4-digit verification code sent by email and marks the account "
        "as active. Requires HTTP Basic authentication (username: email, password: "
        "account password). The operation is idempotent: activating an already-active "
        "account returns 200."
    ),
    responses={
        400: {"model": ErrorDetail, "description": "Code is invalid or has expired."},
        401: {"description": "Invalid credentials."},
        404: {
            "model": ErrorDetail,
            "description": "No verification code found for this user.",
        },
    },
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
