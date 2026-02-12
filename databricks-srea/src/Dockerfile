# Databricks MCP Server - Docker Build from Local Src
# Builds from the src/ folder containing databricks-mcp v0.4.4
# Deployment target: Azure Container Apps

FROM python:3.11-slim

LABEL maintainer="SRE Team"
LABEL description="Databricks MCP Server with Streamable HTTP (Built from src)"

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv venv && uv pip install .

# Expose port 8000 for streamable HTTP transport
EXPOSE 8000

# Environment variables (placeholders, will be overridden by Container Apps Secrets)
ENV DATABRICKS_HOST=""
ENV DATABRICKS_TOKEN=""
ENV DATABRICKS_WAREHOUSE_ID=""
ENV LOG_LEVEL="INFO"
# Configure Uvicorn to bind to all interfaces (required for Docker)
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT="8000"

# Health check (optional, but useful for container orchestrators)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run the application.
CMD ["/app/.venv/bin/python", "/app/entry_http.py"]
