FROM python:3.13-slim-bookworm AS opengrep_builder

RUN apt-get update && \
    apt-get -y install curl

# cosign binary
RUN curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
RUN mv cosign-linux-amd64 /usr/local/bin/cosign
RUN chmod +x /usr/local/bin/cosign

# opengrep binary
RUN curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh -v 1.14.1 | bash

FROM python:3.13-slim-bookworm AS base

ENV PYTHONIOENCODING=utf-8

COPY --from=opengrep_builder /root/.opengrep/cli/latest /app/opengrep

RUN export PATH='/app/opengrep/opengrep':$PATH 

ENTRYPOINT ["/app/opengrep/opengrep"]