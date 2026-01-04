# -----
# STAGE 1: Builder
# -----
FROM python:3.13-slim-bookworm AS builder

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

WORKDIR $PYSETUP_PATH

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-cache

# ----
# STAGE 2: RUNTIME
# ----
FROM python:3.13-slim-bookworm  AS final

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH="/opt/pysetup/.venv" \
    PYTHONPATH="/app/src"

COPY --from=builder $VENV_PATH $VENV_PATH

ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app

COPY src /app/src

USER appuser

EXPOSE 8000

CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "app.main:app"]
