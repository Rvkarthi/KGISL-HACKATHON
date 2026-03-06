from datetime import datetime
from typing import List, Optional

from ninja import Schema
from pydantic import field_validator

from ats.models import JobDescription


class HRRequest(Schema):
    about: str
    skills: List[str]
    soft_skills: List[str]
    languages: List[str]


class FileResult(Schema):
    file_id: str
    filename: str
    status: str  # "success" | "error" | "timeout"
    result: Optional[dict] = None
    error: Optional[str] = None


class BulkScreeningResponse(Schema):
    total: int
    succeeded: int
    failed: int
    results: list[FileResult]


class JobDescriptionIn(Schema):
    title: str
    about: Optional[str] = ""
    experience: Optional[str] = ""
    technical_skills: Optional[str] = ""
    soft_skills: Optional[str] = ""
    languages: Optional[str] = ""
    project_keywords: Optional[str] = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip()

    @field_validator(
        "technical_skills",
        "soft_skills",
        "languages",
        "project_keywords",
        mode="before",
    )
    @classmethod
    def normalize_csv(cls, v):
        """Normalize comma-separated fields: strip spaces around commas."""
        if not v:
            return ""
        return ", ".join(tag.strip() for tag in str(v).split(",") if tag.strip())


class JobDescriptionPatchIn(Schema):
    """All fields optional for partial updates."""

    title: Optional[str] = None
    about: Optional[str] = None
    experience: Optional[str] = None
    technical_skills: Optional[str] = None
    soft_skills: Optional[str] = None
    languages: Optional[str] = None
    project_keywords: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip() if v else v

    @field_validator(
        "technical_skills",
        "soft_skills",
        "languages",
        "project_keywords",
        mode="before",
    )
    @classmethod
    def normalize_csv(cls, v):
        if v is None:
            return None
        return ", ".join(tag.strip() for tag in str(v).split(",") if tag.strip())


class JobFilterIn(Schema):
    """Query params for list endpoint."""

    search: Optional[str] = None  # searches title + about
    is_active: Optional[bool] = None  # filter by active status


# ══════════════════════════════════════════════
# Schemas — Output
# ══════════════════════════════════════════════


class JobDescriptionOut(Schema):
    id: int
    title: str
    about: str
    experience: str
    technical_skills: str
    soft_skills: str
    languages: str
    project_keywords: str
    is_active: bool
    total_submissions: int
    created_at: datetime
    updated_at: datetime

    # Parse CSV fields into clean lists for API consumers
    technical_skills_list: list[str]
    soft_skills_list: list[str]
    languages_list: list[str]
    project_keywords_list: list[str]

    @classmethod
    def from_job(cls, job: JobDescription) -> "JobDescriptionOut":
        def to_list(csv: str) -> list[str]:
            return [x.strip() for x in csv.split(",") if x.strip()] if csv else []

        return cls(
            id=job.id,
            title=job.title,
            about=job.about,
            experience=job.experience,
            technical_skills=job.technical_skills,
            soft_skills=job.soft_skills,
            languages=job.languages,
            project_keywords=job.project_keywords,
            is_active=True,
            total_submissions=getattr(job, "total_submissions", 0),
            created_at=job.created_at,
            updated_at=job.updated_at,
            technical_skills_list=to_list(job.technical_skills),
            soft_skills_list=to_list(job.soft_skills),
            languages_list=to_list(job.languages),
            project_keywords_list=to_list(job.project_keywords),
        )


class JobListOut(Schema):
    id: int
    title: str
    is_active: bool
    total_submissions: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_job(cls, job: JobDescription) -> "JobListOut":
        return cls(
            id=job.id,
            title=job.title,
            is_active=job.is_active,
            total_submissions=getattr(job, "total_submissions", 0),
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class StatsOut(Schema):
    total_jobs: int
    active_jobs: int
    inactive_jobs: int
    total_submissions: int


class MessageOut(Schema):
    message: str


class ErrorOut(Schema):
    detail: str
