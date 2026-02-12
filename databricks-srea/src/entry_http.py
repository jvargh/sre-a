"""
Entry point for running Databricks MCP Server with HTTP transport.
Modifies FastMCP settings to bind to 0.0.0.0 for Docker/ACA compatibility.
Disables DNS rebinding protection for Azure Container Apps reverse proxy.
"""

from databricks_mcp.core.config import settings
from databricks_mcp.core.logging_utils import configure_logging
from databricks_mcp.server.databricks_mcp_server import DatabricksMCPServer
from mcp.server.transport_security import TransportSecuritySettings


def main() -> None:
    """Start MCP server with 0.0.0.0 binding and reverse proxy support."""
    configure_logging(level=settings.LOG_LEVEL, log_file="databricks_mcp.log")
    
    print(f"Starting Databricks MCP Server on 0.0.0.0:8000 (reverse proxy enabled)")
    
    server = DatabricksMCPServer()
    
    # CRITICAL: Override host setting to bind to all interfaces (Docker/ACA requirement)
    server.settings.host = "0.0.0.0"
    server.settings.port = 8000
    
    # CRITICAL: Disable DNS rebinding protection for Azure Container Apps
    # ACA ingress controller modifies the Host header, which triggers false positives
    # This is safe because ACA provides isolation at the infrastructure level
    server.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
    
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
