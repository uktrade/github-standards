FROM python:3.13-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apk update && \
    apk add git

WORKDIR /app

COPY .pre-commit-hooks.yaml /app
COPY pyproject.toml /app
COPY src /app/src

RUN pip install .

ENTRYPOINT ["hooks-cli"]

FROM base AS testing
COPY example.pre-commit-config.yaml /app/.pre-commit-config.yaml

FROM testing AS local-testing
RUN echo 'Hello world' >> /app/EXAMPLE_COMMIT_MSG.txt
