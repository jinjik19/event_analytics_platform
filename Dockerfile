# -----
# STAGE 1: Builder
# -----
FROM python:3.13-slim-bookworm AS builder

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set to "true" to include dev dependencies (for seeder, tests, etc.)
ARG INSTALL_DEV=false

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=120 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

WORKDIR $PYSETUP_PATH

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project --group dev; \
    else \
        uv sync --frozen --no-install-project; \
    fi

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
