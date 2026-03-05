from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserRole(models.TextChoices):
    NORMAL = "normal", "Normal User"
    HR = "hr", "HR"


class UserManager(BaseUserManager):
    """Custom manager that uses email as the unique identifier."""

    def _create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", UserRole.NORMAL)
        return self._create_user(email, password, **extra_fields)

    def create_hr_user(self, email: str, password: str, **extra_fields):
        """Convenience factory for creating HR accounts."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields["role"] = UserRole.HR
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.HR)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.NORMAL,
        db_index=True,
    )
    company = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Organisation name; required for HR accounts.",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        return f"{self.email}"

    @property
    def is_normal_user(self) -> bool:
        return self.role == UserRole.NORMAL

    @property
    def is_hr_user(self) -> bool:
        return self.role == UserRole.HR
