from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RecipientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Recipient name cannot be blank")
        return value


class GenerationJobCreate(BaseModel):
    certificate_title: str = Field(default="Certificate of Completion", min_length=3, max_length=150)
    event_name: str = Field(min_length=2, max_length=200)
    completion_date: date
    issuer_name: str = Field(min_length=2, max_length=150)
    recipients: list[RecipientCreate] = Field(min_length=1, max_length=500)


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_name: str
    recipient_email: str | None
    status: Literal["pending", "success", "failed"]
    error_message: str | None = None
    download_url: str | None = None


class JobResponse(BaseModel):
    id: int
    status: str
    total: int
    successful: int
    failed: int
    progress_percent: float
    certificates: list[CertificateResponse]
