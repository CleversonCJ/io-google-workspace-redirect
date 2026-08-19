FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/CleversonCJ/io-google-workspace-redirect" \
    org.opencontainers.image.description="Nextcloud ExApp that opens Google Workspace pointer files" \
    org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 10001 exapp \
    && useradd --uid 10001 --gid exapp --create-home --shell /usr/sbin/nologin exapp

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --requirement /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY --chown=exapp:exapp ex_app /ex_app

USER exapp
WORKDIR /ex_app/lib

ENTRYPOINT ["python", "main.py"]

HEALTHCHECK --interval=5s --timeout=3s --retries=20 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['APP_PORT'] + '/heartbeat', timeout=2).read()"]
