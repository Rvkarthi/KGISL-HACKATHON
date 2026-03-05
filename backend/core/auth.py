from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import User, UserRole
from core.schemas import RegisterSchema


@transaction.atomic
def create_user(data: RegisterSchema):
    email = data.email.lower()

    if User.objects.filter(email=email).exists():
        raise ValidationError("User with this email already exists.")

    if data.role == UserRole.HR:
        user = User.objects.create_hr_user(
            email=email,
            password=data.password,
            full_name=data.full_name,
            company=data.company,
        )
    else:
        user = User.objects.create_user(
            email=email,
            password=data.password,
            full_name=data.full_name,
        )

    return user


def authenticate_user(email: str, password: str):
    user = authenticate(email=email, password=password)
    if not user:
        return None
    if not user.is_active:
        return None
    return user
