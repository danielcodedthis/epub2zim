# epub2zim: web UI + MCP server in one small container.
#
#   docker build -t epub2zim .
#   docker run -d -p 5100:5100 -v ./data:/data --name epub2zim epub2zim
#
# Settings (all optional):  EPUB2ZIM_PORT, EPUB2ZIM_MCP_KEY, EPUB2ZIM_MCP_AUTH,
# EPUB2ZIM_MAX_UPLOAD_MB, PUID/PGID (owner of the data files).  See docs/configuration.md.

FROM python:3.12-slim

# Python behaves better in containers with these.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EPUB2ZIM_DATA_DIR=/data \
    EPUB2ZIM_HOST=0.0.0.0 \
    EPUB2ZIM_PORT=5100

WORKDIR /app

# Install the app (dependencies first, so code changes rebuild faster).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

# The start script fixes the data folder's owner, then runs the app as user
# PUID:PGID (default 1000:1000, so files in your data folder belong to you).
COPY docker/entrypoint.sh /usr/local/bin/epub2zim-entrypoint
RUN chmod +x /usr/local/bin/epub2zim-entrypoint && mkdir -p /data
ENV PUID=1000 PGID=1000

VOLUME ["/data"]
EXPOSE 5100

# Docker marks the container "healthy" once the web server answers.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"EPUB2ZIM_PORT\",\"5100\")}/api/health', timeout=4)"

ENTRYPOINT ["epub2zim-entrypoint"]
CMD ["epub2zim", "serve"]
