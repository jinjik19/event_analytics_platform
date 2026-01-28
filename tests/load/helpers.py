from datetime import datetime, timedelta, timezone
import string
import uuid
import random

def fast_uuid_hex() -> str:
    return str(uuid.UUID(int=random.getrandbits(128), version=4).hex)


def generate_random_string(length: int = 10) -> str:
    """Generate random string for unique identifiers."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_user_id() -> str | None:
    """Generate user_id. Returns None for 10% of cases (anonymous users)."""
    if random.random() < 0.1:
        return None
    return f"user_{fast_uuid_hex()[:12]}"


def generate_session_id() -> str:
    """Generate session_id."""
    return f"session_{fast_uuid_hex()[:16]}"


def generate_timestamp(max_days_ago: int = 7) -> str:
    """
    Generate timestamp within valid range.

    API constraints:
    - Cannot be in future (max +5 minutes)
    - Cannot be older than 30 days
    """
    now = datetime.now(timezone.utc)
    seconds_ago = random.randint(0, max_days_ago * 24 * 60 * 60)
    timestamp = now - timedelta(seconds=seconds_ago)
    return timestamp.isoformat()
