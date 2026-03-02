from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "supersecret"}
        }
    )

    email: EmailStr = Field(description="User email address. Normalised to lowercase.")
    password: str = Field(
        min_length=8, max_length=128, description="Password (8–128 characters)."
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password", mode="before")
    @classmethod
    def strip_password(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
    )

    id: UUID
    email: EmailStr
    created_at: datetime


class ActivateUserRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"code": "2768"}})

    code: str = Field(
        pattern=r"^\d{4}$",
        description="4-digit numeric verification code sent by email.",
    )
