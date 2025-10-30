# Using a multi-stage image to create a final image without uv.
# First, build the application in the `/app` directory.
ARG TRUFFLEHOG_VERSION='USE_BUILD_ARG'
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv_builder

# This ARG needs to be duplicated here, as the FROM statement above clears the value
ARG TRUFFLEHOG_VERSION
RUN if [ -z "$TRUFFLEHOG_VERSION" ]; then echo 'Environment variable TRUFFLEHOG_VERSION must be specified. Exiting.'; exit 1; fi

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY .pre-commit-hooks.yaml /app
COPY pyproject.toml /app
COPY .python-version /app
COPY uv.lock /app
COPY .config /app
COPY src /app/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Need to make sure we pin a specific version of trufflehog
FROM trufflesecurity/trufflehog:${TRUFFLEHOG_VERSION} AS trufflehog_builder

# # Then, use a final image without uv
FROM python:3.13-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV FORCE_HOOK_CHECKS=1

# Copy the application from the builder
COPY --from=uv_builder /app/.venv /app/.venv
COPY --from=uv_builder /app/.config /app/.config
# Copy the trufflehog runner from the builder
COPY --from=trufflehog_builder /usr/bin/trufflehog /usr/bin/trufflehog

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

ENTRYPOINT ["hooks-cli"]

FROM base AS testing
ENV FORCE_HOOK_CHECKS=0
COPY example.pre-commit-config.yaml /app/.pre-commit-config.yaml
# Copy this folder so we have some python files to scan when testing
COPY src /app/src 
RUN echo 'Hello world commit message' >> /app/EXAMPLE_COMMIT_MSG.txt

FROM base AS release
