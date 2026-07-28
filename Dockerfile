FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/

RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir .

FROM python:3.13-slim

COPY --from=builder /venv /venv

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /home/app/.paprika-mcp \
    && chown -R app:app /home/app/.paprika-mcp

USER app
WORKDIR /home/app

ENTRYPOINT ["/venv/bin/paprika-mcp"]
