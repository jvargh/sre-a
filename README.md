# SRE-A: Azure SRE Agent and Databricks MCP

Comprehensive SRE operations automation using Azure SRE Agent with Model Context Protocol (MCP) integration for Databricks.

This repository includes:
- **Production-ready Databricks MCP server** for Azure SRE Agent
- **SRE Agent assets** (best practices, ops skills, subagent configurations)
- **Deployment guides** and validation tools
- **Example architectures** and runbooks

---

## 📁 Repository Structure

### Core SRE Assets

**[databricks-srea/](databricks-srea/)** — Production Databricks MCP for SRE Agent
- Databricks MCP server built with FastMCP
- 38+ API tools for clusters, jobs, SQL, Unity Catalog, DBFS
- Agent-ready artifacts (best practices, ops skill, subagent config)
- Quickstart deployment guide for Azure Container Apps
- Start here: [databricks-srea/README.md](databricks-srea/README.md)

### Documentation

**[BLOG_POST.md](BLOG_POST.md)** — MCP-Driven Azure SRE for Databricks
- Proactive compliance automation with best practice validation
- Reactive incident response with root cause analysis
- Real-world examples and operational impact metrics

**[zDocs/](zDocs/)** — Architecture and setup guides
- AKS, Azure, and Databricks MCP setup guides
- Integration patterns and best practices

### Example Applications

**[FaultyWebApp/](FaultyWebApp/)** — Azure web application demo
- Deployment, configuration, and troubleshooting examples
- Breakfix guides and runbooks

### Development & Testing

**[zDatabricksMCP/](zDatabricksMCP/)** — MCP server source code
- FastMCP implementation
- API clients and tool registration
- Docker configuration for containerization

**[zDbxSREAgent/](zDbxSREAgent/)** — Agent integration examples
- Operational guides and diagnostic tools
- Incident response patterns

**[zTests/](zTests/)** — Integration and unit tests
- MCP validation tests
- Compliance and remediation checks

---

## 🚀 Quick Start

### Deploy Databricks MCP Server

```bash
cd databricks-srea
# Follow: QUICKSTART_INSTALL.md
# ~30 minutes to deploy to Azure Container Apps
```

### Configure Azure SRE Agent

1. **Upload Knowledge Base** (compliance criteria)
   - File: `databricks-srea/AZURE_DATABRICKS_BEST_PRACTICES.md`
   - Builder > Knowledge Base

2. **Create Ops Skill** (incident runbooks)
   - File: `databricks-srea/DATABRICKS_OPS_RUNBOOK_SKILL.md`
   - Builder > Subagent Builder > Create Skill

3. **Deploy Subagent** (wires MCP + Knowledge + Skill)
   - File: `databricks-srea/Databricks_MCP_Agent.yaml`
   - Agent > Load Configuration

### Validate Setup

```bash
cd databricks-srea
python mcp_validate.py --base-url https://<your-container-app-url> --mode list-tools
python mcp_validate.py --base-url https://<your-container-app-url> --mode validate
```

---

## 📋 Key Capabilities

### Proactive Governance
- ✅ Continuous compliance monitoring against best practices
- ✅ Automated cluster, job, and catalog validation
- ✅ Prioritized remediation recommendations with code examples

### Reactive Incident Response
- 🚨 Root cause analysis for job failures
- 🔍 Automated investigation with evidence and confidence levels
- 🛠️ One-click remediation steps

### Operational Impact
| Metric | Before | After | Improvement |
| --- | --- | --- | --- |
| Compliance review | 2-3 hours | 5 minutes | **95%** |
| Job failure investigation | 30-45 min | 3-8 min | **85%** |
| On-call alerts requiring intervention | 4-6/shift | 1-2/shift | **70%** |

---

## 📚 Resources

### Databricks MCP
- 📘 [Deployment Guide](databricks-srea/QUICKSTART_INSTALL.md)
- 🔧 [MCP Server Architecture](databricks-srea/src/ARCHITECTURE.md)
- 🧪 [Validation Tool](databricks-srea/mcp_validate.py)

### SRE Agent Assets
- 📋 [Best Practices](databricks-srea/AZURE_DATABRICKS_BEST_PRACTICES.md)
- 🧰 [Ops Runbook Skill](databricks-srea/DATABRICKS_OPS_RUNBOOK_SKILL.md)
- 🤖 [Subagent Configuration](databricks-srea/Databricks_MCP_Agent.yaml)

### Blog & Learning
- 📖 [Blog: MCP-Driven Azure SRE for Databricks](BLOG_POST.md)
- 📚 [Microsoft Azure SRE Docs](https://learn.microsoft.com/en-us/azure/sre-agent/)
- 🌐 [MCP Specification](https://modelcontextprotocol.io/specification/)

---

## 🛠️ Development

### Prerequisites
- Python 3.10+
- Azure CLI
- Docker
- Git

### Clone & Install

```bash
git clone https://github.com/jvargh/sre-a.git
cd sre-a/databricks-srea

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp src/.env.example .env
# Edit .env with your Databricks credentials
```

### Run Locally

```bash
cd src
python entry_http.py
# Server runs on http://localhost:8000
```

---

## 📞 Support & Contributing

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: See [databricks-srea/README.md](databricks-srea/README.md) for detailed MCP server docs

---

## 📄 License

Specify your license here.

---

**Built for SRE teams automating Azure Databricks operations with intelligence and speed.**
