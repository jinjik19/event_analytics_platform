import secrets


def generate_api_key(env: str) -> str:
    random_part = secrets.token_urlsafe(32)
    new_api_key = f"wk_{env}_{random_part}"

    return new_api_key
