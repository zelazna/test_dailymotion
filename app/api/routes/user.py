from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash

from app.api.depends import get_db
from app.api.models.user import UserCreate, UserResponse
from app.db.user import UniqueViolationError, create_user

router = APIRouter()

_password_hash = PasswordHash.recommended()


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    body: UserCreate,
    conn: Annotated[Connection, Depends(get_db)],
) -> UserResponse:
    password_hash = _password_hash.hash(body.password)
    try:
        user = await create_user(conn, body.email, password_hash)
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
        )
    except UniqueViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
