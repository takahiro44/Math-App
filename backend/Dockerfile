FROM python:3.11.9-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y \
    fonts-ipafont \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .