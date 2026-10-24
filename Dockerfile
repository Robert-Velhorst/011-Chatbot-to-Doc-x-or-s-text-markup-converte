FROM node:26.12.1-trixie-slim@sha256:36793bcbb160a6a16cede1e62b93f84e26b78a972a8a4c0b879c1c12f22761ec AS web
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --global npm@12.2.1 && npm ci --ignore-scripts && npm audit --audit-level=low
COPY studio-ui ./studio-ui
RUN npm run studio:build

FROM python:3.15.1-slim-trixie@sha256:08275f764e022331c6d3e3ca55d8cce01fa4684b02111adf0445d71806fe7941 AS dependencies
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/studio ./src/studio
RUN python -m pip install --no-cache-dir uv==0.13.5 && uv sync --frozen --no-dev --no-editable

FROM python:3.15.1-slim-trixie@sha256:08275f764e022331c6d3e3ca55d8cce01fa4684b02111adf0445d71806fe7941 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CLEAN_PASTE_HOST=0.0.0.0 CLEAN_PASTE_PORT=8765 CLEAN_PASTE_ENV=production PATH=/app/.venv/bin:$PATH
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=dependencies /app/.venv ./.venv
COPY --from=web /app/studio-ui/dist ./studio-ui/dist
RUN useradd --create-home --uid 10001 studio && mkdir -p /data && chown -R studio:studio /data /app
USER studio
ENV CLEAN_PASTE_DATA_DIR=/data CLEAN_PASTE_UI_DIR=/app/studio-ui/dist
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=2)"]
CMD ["python", "-m", "cleanpaste_studio", "serve"]
