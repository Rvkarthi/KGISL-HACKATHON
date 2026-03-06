from django.contrib.auth.models import AbstractUser
from django.db import models


class HRUser(AbstractUser):
    """
    Custom user model for HR accounts.
    Each HR gets their own isolated portal.
    """

    company_name = models.CharField(max_length=255)
    portal_slug = models.SlugField(
        unique=True, help_text="Unique URL slug for the HR's candidate portal"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} — {self.company_name}"
