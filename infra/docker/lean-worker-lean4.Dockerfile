# Lean 4 worker image for container runner. Use for OBR_WORKER_RUNNER=container when
# real lake/lean are required. Base image has elan, lake, and lean in PATH.
# Build from repo root: docker build -f infra/docker/lean-worker-lean4.Dockerfile -t lean-worker:test .
FROM leanprovercommunity/lean4:latest

COPY infra/docker/lean-worker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
