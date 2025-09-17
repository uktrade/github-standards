FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apk update && \
    apk add git

WORKDIR /app
COPY . /app

RUN pip install .
