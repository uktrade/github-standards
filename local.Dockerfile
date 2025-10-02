# This file is here as a simpler dockerfile for quickly building a docker image that can be used for testing code
# inside a docker container
FROM python:3.13-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY .pre-commit-hooks.yaml /app
COPY pyproject.toml /app
COPY .python-version /app
COPY uv.lock /app
COPY src /app/src

RUN pip install uv
RUN uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["hooks-cli"]

FROM base AS local-testing
COPY example.pre-commit-config.yaml /app/.pre-commit-config.yaml
RUN echo 'Hello world commit message' >> /app/EXAMPLE_COMMIT_MSG.txt