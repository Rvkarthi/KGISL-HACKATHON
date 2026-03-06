import re
from typing import Optional

from django.contrib.auth.password_validation import validate_password
from ninja import Schema
from pydantic import BaseModel, field_validator, model_validator

from core.models import HRUser

# ══════════════════════════════════════════════
# Schemas — Input
# ══════════════════════════════════════════════


class RegisterIn(Schema):
    username: str
    email: str
    password: str
    confirm_password: str
    company_name: str
    portal_slug: Optional[str] = None  # Auto-generated from company_name if omitted

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not re.match(r"^\w+$", v):
            raise ValueError(
                "Username must be alphanumeric (letters, digits, underscores)"
            )
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.lower()

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginIn(BaseModel):
    username: str  # username or email
    password: str


class RefreshIn(BaseModel):
    refresh: str


class LogoutIn(BaseModel):
    refresh: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        return self


class UpdateProfileIn(BaseModel):
    company_name: Optional[str] = None
    email: Optional[str] = None
    portal_slug: Optional[str] = None

    @field_validator("portal_slug")
    @classmethod
    def slug_valid(cls, v):
        if v and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Portal slug can only contain lowercase letters, numbers, and hyphens"
            )
        return v


# ══════════════════════════════════════════════
# Schemas — Output
# ══════════════════════════════════════════════


class TokenOut(BaseModel):
    access: str
    refresh: str
    token_type: str = "bearer"


class HRProfileOut(BaseModel):
    id: int
    username: str
    email: str
    company_name: str
    portal_slug: str
    is_active: bool
    date_joined: str
    created_at: str

    @classmethod
    def from_user(cls, user: HRUser) -> "HRProfileOut":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            company_name=user.company_name,
            portal_slug=user.portal_slug,
            is_active=user.is_active,
            date_joined=user.date_joined.isoformat(),
            created_at=user.created_at.isoformat(),
        )


class MessageOut(BaseModel):
    message: str


class ErrorOut(BaseModel):
    detail: str
