from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

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
    id: UUID
    email: EmailStr
    created_at: datetime


class ActivateUserRequest(BaseModel):
    code: str = Field(pattern=r"^\d{4}$")  # Limit to 4 digits
