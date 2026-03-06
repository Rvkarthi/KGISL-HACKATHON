import uuid

from core.models import HRUser
from django.db import models

# ─────────────────────────────────────────────
# 2. Job Description (created & owned by HR)
# ─────────────────────────────────────────────


class JobDescription(models.Model):
    """
    HR customizes and creates job descriptions.
    Only accessible by the HR who created it.
    """

    hr = models.ForeignKey(
        HRUser, on_delete=models.CASCADE, related_name="job_descriptions"
    )
    title = models.CharField(max_length=255)
    # ── Core JD Fields ──────────────────────────
    about = models.TextField(blank=True, help_text="Role overview / company intro")
    experience = models.TextField(
        blank=True, help_text="Years and type of experience required"
    )
    # ── Structured Skill Fields ─────────────────
    # Stored as comma-separated text or use ArrayField if on PostgreSQL
    technical_skills = models.TextField(
        blank=True, help_text="e.g. Python, Django, React"
    )
    soft_skills = models.TextField(
        blank=True, help_text="e.g. Communication, Leadership"
    )
    languages = models.TextField(
        blank=True, help_text="e.g. English (Fluent), Tamil (Native)"
    )
    project_keywords = models.TextField(
        blank=True, help_text="Keywords to look for in candidate projects"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # Ensures HR can only see their own JDs — enforce in views/queryset too
        verbose_name = "Job Description"

    def __str__(self):
        return f"[{self.hr.company_name}] {self.title}"


# ─────────────────────────────────────────────
# 3. Candidate Submission
# ─────────────────────────────────────────────


class CandidateSubmission(models.Model):
    """
    Stores each candidate's submission for a specific job.
    Linked to the HR portal via the JobDescription.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("scored", "Scored"),
        ("rejected", "Rejected"),
        ("shortlisted", "Shortlisted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        JobDescription, on_delete=models.CASCADE, related_name="submissions"
    )

    # ── Candidate Info ───────────────────────────
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # ── Original Resume ──────────────────────────
    resume_file = models.FileField(
        upload_to="resumes/original/%Y/%m/",
        help_text="Original uploaded resume (PDF/DOCX)",
    )
    resume_text = models.TextField(
        blank=True, help_text="Extracted raw text from resume (for ATS parsing)"
    )

    # ── ATS Result ───────────────────────────────
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    ats_score = models.FloatField(
        null=True, blank=True, help_text="Overall ATS match score (0–100)"
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = [("job", "email")]  # One submission per candidate per job

    def __str__(self):
        return f"{self.full_name} → {self.job.title} ({self.ats_score or 'pending'})"


# ─────────────────────────────────────────────
# 4. ATS Score Breakdown (per section)
# ─────────────────────────────────────────────


class ATSResult(models.Model):
    """
    Detailed ATS scoring breakdown for each submission.
    One-to-one with CandidateSubmission.
    """

    submission = models.OneToOneField(
        CandidateSubmission, on_delete=models.CASCADE, related_name="ats_result"
    )

    # ── Per-section scores (0–100) ───────────────
    skills_score = models.FloatField(null=True, blank=True)
    soft_skills_score = models.FloatField(null=True, blank=True)
    experience_score = models.FloatField(null=True, blank=True)
    language_score = models.FloatField(null=True, blank=True)
    projects_score = models.FloatField(null=True, blank=True)

    # ── Matched / Missing keywords ───────────────
    matched_skills = models.TextField(
        blank=True, help_text="Comma-separated matched skills"
    )
    missing_skills = models.TextField(
        blank=True, help_text="Comma-separated skills not found in resume"
    )
    # ── AI / Parser feedback ─────────────────────
    summary_feedback = models.TextField(
        blank=True, null=True, help_text="Short AI-generated summary of candidate fit"
    )
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ATSResult for {self.submission.full_name} — Score: {self.submission.ats_score}"
