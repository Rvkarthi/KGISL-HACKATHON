# django auth

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from ninja import Router
from ninja.security import HttpBearer
from ninja_jwt.exceptions import TokenError
from ninja_jwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from ninja_jwt.tokens import AccessToken, RefreshToken

# models
from core.models import HRUser

# schemas
from core.schemas import (
    ChangePasswordIn,
    ErrorOut,
    HRProfileOut,
    LoginIn,
    LogoutIn,
    MessageOut,
    RefreshIn,
    RegisterIn,
    TokenOut,
    UpdateProfileIn,
)

router = Router(tags=["HR Auth"])


# ══════════════════════════════════════════════
# Security — Bearer token auth
# ══════════════════════════════════════════════


class JWTAuth(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            access = AccessToken(token)
            user_id = access["user_id"]
            user = HRUser.objects.get(id=user_id, is_active=True)
            request.user = user
            return user
        except (TokenError, HRUser.DoesNotExist):
            return None


auth = JWTAuth()


# ══════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════


def _get_tokens(user: HRUser) -> dict:
    """Generate access + refresh token pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _unique_slug(base_slug: str) -> str:
    """Ensure portal_slug is unique, appending suffix if needed."""
    slug = slugify(base_slug)[:48]
    candidate = slug
    counter = 1
    while HRUser.objects.filter(portal_slug=candidate).exists():
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


# ══════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════


@router.post("/register", response={201: TokenOut, 400: ErrorOut}, auth=None)
def register(request, payload: RegisterIn):
    """Register a new HR account and return tokens immediately."""

    # ── Uniqueness checks ────────────────────────
    if HRUser.objects.filter(username=payload.username).exists():
        return 400, {"detail": "Username already taken"}

    if HRUser.objects.filter(email=payload.email).exists():
        return 400, {"detail": "Email already registered"}

    # ── Password validation (Django built-in validators) ──
    try:
        validate_password(payload.password)
    except ValidationError as e:
        return 400, {"detail": " | ".join(e.messages)}

    # ── Resolve portal slug ──────────────────────
    slug = payload.portal_slug or payload.company_name
    portal_slug = _unique_slug(slug)

    # ── Create user ──────────────────────────────
    user = HRUser.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        company_name=payload.company_name,
        portal_slug=portal_slug,
    )

    return 201, _get_tokens(user)


@router.post("/login", response={200: TokenOut, 401: ErrorOut}, auth=None)
def login(request, payload: LoginIn):
    """Authenticate HR user and return JWT tokens."""

    # Support login via username OR email
    username = payload.username
    if "@" in payload.username:
        try:
            username = HRUser.objects.get(email=payload.username.lower()).username
        except HRUser.DoesNotExist:
            return 401, {"detail": "Invalid credentials"}

    user = authenticate(request, username=username, password=payload.password)

    if user is None:
        return 401, {"detail": "Invalid credentials"}

    if not user.is_active:
        return 401, {"detail": "Account is deactivated. Please contact support."}

    return 200, _get_tokens(user)


@router.post("/token/refresh", response={200: dict, 401: ErrorOut}, auth=None)
def refresh_token(request, payload: RefreshIn):
    """Get a new access token using a valid refresh token."""
    try:
        refresh = RefreshToken(payload.refresh)
        return 200, {
            "access": str(refresh.access_token),
            "token_type": "bearer",
        }
    except TokenError as e:
        return 401, {"detail": str(e)}


@router.post("/logout", response={200: MessageOut, 400: ErrorOut}, auth=auth)
def logout(request, payload: LogoutIn):
    """Blacklist the refresh token to invalidate the session."""
    try:
        token = RefreshToken(payload.refresh)
        token.blacklist()
        return 200, {"message": "Logged out successfully"}
    except TokenError as e:
        return 400, {"detail": str(e)}


@router.get("/me", response={200: HRProfileOut, 401: ErrorOut}, auth=auth)
def get_profile(request):
    """Return the currently authenticated HR's profile."""
    return 200, HRProfileOut.from_user(request.user)


@router.patch("/me", response={200: HRProfileOut, 400: ErrorOut}, auth=auth)
def update_profile(request, payload: UpdateProfileIn):
    """Update HR profile fields (email, company_name, portal_slug)."""
    user: HRUser = request.user
    data = payload.model_dump(exclude_unset=True)

    if "email" in data:
        email = data["email"].lower()
        if HRUser.objects.exclude(pk=user.pk).filter(email=email).exists():
            return 400, {"detail": "Email already in use by another account"}
        user.email = email

    if "company_name" in data:
        user.company_name = data["company_name"]

    if "portal_slug" in data:
        slug = data["portal_slug"]
        if HRUser.objects.exclude(pk=user.pk).filter(portal_slug=slug).exists():
            return 400, {"detail": "Portal slug already taken"}
        user.portal_slug = slug

    user.save()
    return 200, HRProfileOut.from_user(user)


@router.post("/change-password", response={200: MessageOut, 400: ErrorOut}, auth=auth)
def change_password(request, payload: ChangePasswordIn):
    """Change the authenticated HR's password and invalidate all existing tokens."""
    user: HRUser = request.user

    if not user.check_password(payload.old_password):
        return 400, {"detail": "Old password is incorrect"}

    try:
        validate_password(payload.new_password, user=user)
    except ValidationError as e:
        return 400, {"detail": " | ".join(e.messages)}

    user.set_password(payload.new_password)
    user.save()

    # ── Blacklist all outstanding refresh tokens for this user ──
    tokens = OutstandingToken.objects.filter(user=user)
    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)

    return 200, {"message": "Password changed successfully. Please log in again."}
