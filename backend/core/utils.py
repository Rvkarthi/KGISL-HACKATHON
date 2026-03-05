from ninja.errors import HttpError
from ninja.security import HttpBearer
from ninja_jwt.exceptions import InvalidToken, TokenError
from ninja_jwt.tokens import AccessToken

from core.models import User


class AuthBearer(HttpBearer):
    """
    Validates Bearer JWT access tokens and attaches the User to request.auth.
    """

    def authenticate(self, request, token: str):
        try:
            validated = AccessToken(token)
        except (TokenError, InvalidToken):
            raise HttpError(401, "Invalid or expired access token.")

        user_id = validated.get("user_id")
        try:
            user = User.objects.select_related("student_profile", "hr_profile").get(
                pk=user_id, is_active=True
            )
        except User.DoesNotExist:
            raise HttpError(401, "User not found or inactive.")

        return user
