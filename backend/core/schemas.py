from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from core.models import User

# ── Register ───────────────────────────────────────────────────────────────────


class RegisterNormalUserSchema(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name must not be blank.")
        return v.strip()

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterNormalUserSchema":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class RegisterHRUserSchema(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    confirm_password: str
    company_name: str
    department: Optional[str] = None
    job_title: Optional[str] = None

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterHRUserSchema":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


# ── Login ──────────────────────────────────────────────────────────────────────


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenPairSchema(BaseModel):
    access: str
    refresh: str


class RefreshSchema(BaseModel):
    refresh: str


class AccessTokenSchema(BaseModel):
    access: str


# ── User Out ───────────────────────────────────────────────────────────────────


class StudentProfileOut(BaseModel):
    university: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    class Config:
        from_attributes = True


class HRProfileOut(BaseModel):
    company_name: str
    department: Optional[str] = None
    job_title: Optional[str] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    student_profile: Optional[StudentProfileOut] = None
    hr_profile: Optional[HRProfileOut] = None

    class Config:
        from_attributes = True


# ── Update Profile ─────────────────────────────────────────────────────────────


class UpdateStudentProfileSchema(BaseModel):
    university: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class UpdateHRProfileSchema(BaseModel):
    department: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None


# ── Change Password ────────────────────────────────────────────────────────────


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordSchema":
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        return self
