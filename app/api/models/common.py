from pydantic import BaseModel


class ErrorDetail(BaseModel):
    detail: str


class StatusResponse(BaseModel):
    status: str
