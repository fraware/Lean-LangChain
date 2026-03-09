FROM python:3.12-slim

RUN useradd -m obr
USER obr
WORKDIR /home/obr/app

COPY infra/docker/lean-worker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
