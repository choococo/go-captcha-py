FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

# Install dependencies first so source-only changes can reuse the Docker cache.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project --extra fastapi

COPY src ./src
COPY examples ./examples

# Install the local package after copying source code.
RUN uv sync --frozen --no-dev --extra fastapi

EXPOSE 9000

CMD ["/app/.venv/bin/uvicorn", "examples.fastapi_server:app", "--host", "0.0.0.0", "--port", "9000"]
