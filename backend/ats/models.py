import json
import uuid

from core.models import User
from django.db import models

# ── Enums ──────────────────────────────────────────────────────────────────────


class ApplicationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    REVIEWED = "reviewed", "Reviewed"
    SHORTLISTED = "shortlisted", "Shortlisted"
    REJECTED = "rejected", "Rejected"
    ACCEPTED = "accepted", "Accepted"


# ── Student Profile ────────────────────────────────────────────────────────────


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    university = models.CharField(max_length=255, blank=True, null=True)
    degree = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Profile"

    def __str__(self):
        return f"StudentProfile({self.user.email})"


# ── HR Profile ─────────────────────────────────────────────────────────────────


class HRProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="hr_profile"
    )
    company_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "HR Profile"

    def __str__(self):
        return f"HRProfile({self.user.email} @ {self.company_name})"


# ── Resume ─────────────────────────────────────────────────────────────────────


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="resumes"
    )
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255)
    # SQLite: store JSON as text, use the property helpers below
    parsed_data = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resume"

    def __str__(self):
        return f"Resume({self.file_name})"

    # ── JSON helpers ──────────────────────────────────────────────────────────
    @property
    def parsed_data_json(self):
        return json.loads(self.parsed_data) if self.parsed_data else None

    @parsed_data_json.setter
    def parsed_data_json(self, value):
        self.parsed_data = json.dumps(value) if value is not None else None


# ── Job ────────────────────────────────────────────────────────────────────────


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hr = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jobs",
        help_text="The HR user who posted this job.",
    )
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    requirements = models.TextField()
    # SQLite: store JSON as text, use the property helper below
    skills_required = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job({self.title})"

    # ── JSON helpers ──────────────────────────────────────────────────────────
    @property
    def skills_required_json(self):
        return json.loads(self.skills_required) if self.skills_required else []

    @skills_required_json.setter
    def skills_required_json(self, value):
        self.skills_required = json.dumps(value) if value is not None else None


# ── Application ────────────────────────────────────────────────────────────────


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.ForeignKey(
        Resume, on_delete=models.SET_NULL, null=True, related_name="applications"
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        db_index=True,
    )
    ats_match_score = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    hr_private_notes = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Application"
        unique_together = [("job", "student")]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"Application({self.student} → {self.job})"


# ── Application History ────────────────────────────────────────────────────────


class ApplicationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="history"
    )
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_changes",
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Application History"
        ordering = ["-created_at"]

    def __str__(self):
        return f"History({self.id} → {self.status})"
