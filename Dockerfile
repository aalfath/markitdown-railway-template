# MarkItDown v0.1.8 as an authenticated REST + MCP (Streamable HTTP) service.
FROM python:3.13-slim-trixie@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install "markitdown[all]==0.1.8" "mcp==2.2.0" "uvicorn==0.53.0" "python-multipart==0.0.32" \
 && useradd --system --uid 10001 --home-dir /app markitdown
WORKDIR /app
COPY server.py /app/server.py
USER markitdown
EXPOSE 8080
CMD ["python", "/app/server.py"]
