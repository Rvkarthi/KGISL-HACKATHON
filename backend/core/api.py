from ats.models import HRProfile, StudentProfile
from django.contrib.auth import authenticate
from django.db import transaction
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.tokens import RefreshToken

from core.models import User, UserRole
from core.schemas import (
    AccessTokenSchema,
    ChangePasswordSchema,
    LoginSchema,
    RefreshSchema,
    RegisterHRUserSchema,
    RegisterNormalUserSchema,
    TokenPairSchema,
    UpdateHRProfileSchema,
    UpdateStudentProfileSchema,
    UserOut,
)
from core.utils import AuthBearer

router = Router(tags=["Auth"])


# ── Helpers ────────────────────────────────────────────────────────────────────


def _token_pair(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ── Register ───────────────────────────────────────────────────────────────────


@router.post(
    "/register/normal", response=TokenPairSchema, summary="Register a normal user"
)
@transaction.atomic
def register_normal(request, payload: RegisterNormalUserSchema):
    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "A user with this email already exists.")

    user = User.objects.create_user(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=UserRole.NORMAL,
    )
    StudentProfile.objects.create(user=user)
    return _token_pair(user)


@router.post("/register/hr", response=TokenPairSchema, summary="Register an HR user")
@transaction.atomic
def register_hr(request, payload: RegisterHRUserSchema):
    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "A user with this email already exists.")

    user = User.objects.create_user(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=UserRole.HR,
        company=payload.company_name,
    )
    HRProfile.objects.create(
        user=user,
        company_name=payload.company_name,
        department=payload.department,
        job_title=payload.job_title,
    )
    return _token_pair(user)


# ── Login ──────────────────────────────────────────────────────────────────────


@router.post("/login", response=TokenPairSchema, summary="Login with email & password")
def login(request, payload: LoginSchema):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid credentials.")
    if not user.is_active:
        raise HttpError(403, "Account is disabled.")
    return _token_pair(user)


# ── Token Refresh ──────────────────────────────────────────────────────────────


@router.post(
    "/token/refresh", response=AccessTokenSchema, summary="Refresh access token"
)
def token_refresh(request, payload: RefreshSchema):
    try:
        refresh = RefreshToken(payload.refresh)
        return {"access": str(refresh.access_token)}
    except Exception:
        raise HttpError(401, "Invalid or expired refresh token.")


# ── Me / Profile ───────────────────────────────────────────────────────────────


@router.get("/me", response=UserOut, auth=AuthBearer(), summary="Get current user")
def me(request):
    user = request.auth
    # Prefetch related profiles to avoid N+1
    if user.is_normal_user:
        try:
            _ = user.student_profile
        except StudentProfile.DoesNotExist:
            StudentProfile.objects.create(user=user)
    return user


@router.patch(
    "/me/profile", response=UserOut, auth=AuthBearer(), summary="Update profile"
)
@transaction.atomic
def update_profile(
    request, payload: UpdateStudentProfileSchema | UpdateHRProfileSchema
):
    user = request.auth

    if user.is_normal_user:
        if not isinstance(payload, UpdateStudentProfileSchema):
            raise HttpError(400, "Use the student profile schema.")
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        for field, value in payload.dict(exclude_none=True).items():
            setattr(profile, field, value)
        profile.save()

    elif user.is_hr_user:
        if not isinstance(payload, UpdateHRProfileSchema):
            raise HttpError(400, "Use the HR profile schema.")
        profile, _ = HRProfile.objects.get_or_create(
            user=user, defaults={"company_name": user.company}
        )
        for field, value in payload.dict(exclude_none=True).items():
            setattr(profile, field, value)
        profile.save()

    return user


@router.post("/me/change-password", auth=AuthBearer(), summary="Change password")
def change_password(request, payload: ChangePasswordSchema):
    user = request.auth
    if not user.check_password(payload.old_password):
        raise HttpError(400, "Old password is incorrect.")
    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    return {"detail": "Password updated successfully."}


# ── Logout (blacklist refresh token) ──────────────────────────────────────────


@router.post("/logout", auth=AuthBearer(), summary="Logout (blacklist refresh token)")
def logout(request, payload: RefreshSchema):
    try:
        token = RefreshToken(payload.refresh)
        token.blacklist()
    except Exception:
        raise HttpError(400, "Invalid token.")
    return {"detail": "Successfully logged out."}
