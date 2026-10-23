FROM node:26.12.1-bookworm-slim@sha256:28147155d47dc31abe0a46e0d12b59b2fb3d0a2dcc5dc65fce76a074180b16fe AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --global npm@12.2.1 && npm ci
COPY studio-ui ./studio-ui
RUN npm run studio:build

FROM python:3.15.0-slim-bookworm@sha256:2a41267d9de9d358f77a1de356e0f16ecba8d39827855be0ce9ef4792edce402 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CLEAN_PASTE_HOST=0.0.0.0 CLEAN_PASTE_PORT=8765 CLEAN_PASTE_ENV=production
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/studio ./src/studio
COPY --from=web /app/studio-ui/dist ./studio-ui/dist
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 studio && mkdir -p /data && chown -R studio:studio /data /app
USER studio
ENV CLEAN_PASTE_DATA_DIR=/data CLEAN_PASTE_UI_DIR=/app/studio-ui/dist
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=2)"]
CMD ["python", "-m", "cleanpaste_studio", "serve"]
