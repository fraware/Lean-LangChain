# Minimal Python-only worker image (no Lean). Use when workers only run Python entrypoints.
# For lake/lean builds use lean-worker.Dockerfile (default) or lean-worker-lean4.Dockerfile.
FROM python:3.12-slim

RUN useradd -m obr
USER obr
WORKDIR /home/obr

COPY infra/docker/lean-worker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
