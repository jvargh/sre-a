# Databricks MCP for Azure SRE Agent

Production-ready Databricks MCP server plus SRE Agent assets for proactive compliance and reactive incident response. This repo includes:

- Databricks MCP server source (in [src/](src/))
- Quickstart deployment guide for Azure Container Apps
- Validation script to test MCP endpoints
- SRE Agent assets (best practices, ops runbook skill, and subagent config)

## What this repo does

- Exposes Databricks REST APIs as MCP tools (clusters, jobs, SQL, Unity Catalog, DBFS, repos)
- Supports SRE Agent workflows for best-practice validation and incident RCA
- Provides agent-ready artifacts to standardize compliance and on-call responses

## Quickstart

For full deployment and integration steps, see [QUICKSTART_INSTALL.md](QUICKSTART_INSTALL.md).

Typical flow:
1. Build and deploy MCP server to Azure Container Apps
2. Configure secrets and Databricks credentials
3. Validate MCP endpoint using [mcp_validate.py](mcp_validate.py)
4. Wire up Azure SRE Agent using the assets in this repo

## Repository layout

### Root files

- [AZURE_DATABRICKS_BEST_PRACTICES.md](AZURE_DATABRICKS_BEST_PRACTICES.md)
  - Agent-executable best practices covering reliability, security, cost, ops, performance, and Unity Catalog.
  - Upload via Builder > Knowledge Base for compliance checks and remediation guidance.

- [DATABRICKS_OPS_RUNBOOK_SKILL.md](DATABRICKS_OPS_RUNBOOK_SKILL.md)
  - Ops runbook skill for incident timelines, escalation rules, and audit logging.
  - Create via Builder > Subagent Builder > Create skill and drop this file.

- [Databricks_MCP_Agent.yaml](Databricks_MCP_Agent.yaml)
  - Subagent configuration that connects MCP tools + Knowledge Base + Ops Skill.
  - Enables proactive compliance and reactive RCA in one agent.

- [mcp_validate.py](mcp_validate.py)
  - CLI validation tool for MCP endpoints. Supports initialize, tool listing, and validation checks.

- [QUICKSTART_INSTALL.md](QUICKSTART_INSTALL.md)
  - End-to-end deployment guide for Azure Container Apps, including testing and troubleshooting.

- [DEPLOYMENT_STEPS_SRC.md](DEPLOYMENT_STEPS_SRC.md)
  - Legacy notes. Retained for reference only.

### Source code (src/)

- [src/README.md](src/README.md)
  - Detailed MCP server documentation: capabilities, configuration, running, testing.

- [src/ARCHITECTURE.md](src/ARCHITECTURE.md)
  - Deep dive on runtime design, tool registration, error handling, and data flow.

- [src/AGENTS.md](src/AGENTS.md)
  - Repository guidelines and conventions for contributors.

- [src/Dockerfile](src/Dockerfile)
  - Container image definition for the MCP server.

- [src/entry_http.py](src/entry_http.py)
  - HTTP entrypoint for streamable MCP transport (Container Apps deployment).

- [src/pyproject.toml](src/pyproject.toml)
  - Python packaging and dependency metadata.

- [src/.env.example](src/.env.example)
  - Example environment variables for local or container runs.

- [src/databricks_mcp/](src/databricks_mcp/)
  - Core MCP server implementation.
  - api/: thin clients for Databricks REST endpoints
  - core/: settings, logging, models, HTTP utils
  - server/: FastMCP server, tool registration, helpers
  - cli/: command entrypoints

- [src/tests/](src/tests/)
  - Unit and integration-style tests for tools, structured responses, and metadata.

## Validation

Use [mcp_validate.py](mcp_validate.py) to verify the MCP endpoint:

```bash
python mcp_validate.py --base-url https://<container-app-url> --mode list-tools
python mcp_validate.py --base-url https://<container-app-url> --mode validate --warehouse-id <id>
```

## SRE Agent integration assets

- Best Practices doc -> Knowledge Base (compliance criteria)
- Ops Runbook Skill -> Skill library (incident timelines and escalation)
- Databricks_MCP_Agent -> Subagent (connects MCP + knowledge + ops skill)

## Support

- Deployment troubleshooting: [QUICKSTART_INSTALL.md](QUICKSTART_INSTALL.md)
- MCP server internals: [src/README.md](src/README.md) and [src/ARCHITECTURE.md](src/ARCHITECTURE.md)

## License

Specify the license for your distribution here.
