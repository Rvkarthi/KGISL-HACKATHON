# django
# typing
from typing import Dict

from django.core.exceptions import ValidationError

# ninja
from ninja import Router
from ninja.errors import HttpError

# ninja jwt
from ninja_jwt.tokens import RefreshToken

# custom
from core.auth import authenticate_user, create_user
from core.schemas import LoginSchema, RegisterSchema, UserOutSchema

# authentication
router = Router(tags=["authenication"])


@router.post("/register", response={200: UserOutSchema, 400: dict})
def register_user(request, playload: RegisterSchema) -> Dict:

    try:
        user = create_user(playload)
    except ValidationError as error:
        raise HttpError(status_code=400, message=str(error))

    return 200, user


# ---------------------------
# Login
# ---------------------------


@router.post("/login", response={200: dict, 401: dict})
def login(request, payload: LoginSchema):

    user = authenticate_user(payload.email, payload.password)

    if not user:
        raise HttpError(status_code=401, message="Invalid credentials")

    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
    }
