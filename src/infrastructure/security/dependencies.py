from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Request

from domain.exceptions.app import ForbiddenError
from infrastructure.security.token_validators.secret_token_validator import SecretTokenValidator


@inject
async def token_auth_required(
    request: Request,
    validator: FromDishka[SecretTokenValidator],
) -> None:
    authorization = request.headers.get("Authorization")
    if authorization is None:
        raise ForbiddenError(message="Missing Authorization header")

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise ForbiddenError(message="Invalid authorization header format")
    token = authorization.removeprefix(prefix)
    if not validator.validate(token):
        raise ForbiddenError(message="Invalid secret token")
