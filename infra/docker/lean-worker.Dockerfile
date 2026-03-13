# Default Lean worker image: Lean-capable base so OBR_WORKER_RUNNER=container works
# for real lake/lean builds. Uses leanprovercommunity/lean4 (elan, lake, lean in PATH).
# For a minimal Python-only image use lean-worker-slim.Dockerfile and install Lean in your own stage.
FROM leanprovercommunity/lean4:latest

COPY infra/docker/lean-worker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
