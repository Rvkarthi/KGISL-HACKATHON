from typing import Optional

from ninja import Schema
from pydantic import EmailStr, Field, validator

from core.models import UserRole


class RegisterSchema(Schema):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    role: UserRole
    company: Optional[str] = ""

    @validator("company", always=True)
    def validate_company_for_hr(cls, v, values):
        role = values.get("role")
        if role == UserRole.HR and not v:
            raise ValueError("Company is required for HR users.")
        return v


class LoginSchema(Schema):
    email: EmailStr
    password: str


class UserOutSchema(Schema):
    email: EmailStr
    full_name: str
    role: UserRole
    company: Optional[str]
