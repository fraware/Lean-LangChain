# Obligation Runtime Lean Gateway — production image
# Build from repo root: docker build -f infra/docker/gateway.Dockerfile -t obligation-gateway:latest .
# Multi-stage: builder installs deps; final runs as non-root with HEALTHCHECK.
#
# Pinned deps: For reproducible builds, use a lockfile. If the repo has uv.lock at root (or a
# workspace that includes the gateway), copy it and run `uv sync --frozen` in the builder instead
# of pip install; then copy the resulting site-packages to runtime. Otherwise use the same
# COPY/RUN below and pin critical dependency versions in pyproject.toml.

# --- Builder: install schemas + gateway with postgres extra ---
FROM python:3.12-slim AS builder

WORKDIR /build

COPY packages/schemas/pyproject.toml packages/schemas/
COPY packages/schemas/lean_langchain_schemas packages/schemas/lean_langchain_schemas/
COPY apps/lean-gateway/pyproject.toml apps/lean-gateway/
COPY apps/lean-gateway/lean_langchain_gateway apps/lean-gateway/lean_langchain_gateway/

RUN pip install --no-cache-dir ./packages/schemas "./apps/lean-gateway[postgres]"

# --- Final: minimal runtime ---
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 obr && useradd --uid 1000 --gid obr --shell /bin/false obr

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

ENV PYTHONUNBUFFERED=1

RUN chown -R obr:obr /app

EXPOSE 8000

USER obr

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "lean_langchain_gateway.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
