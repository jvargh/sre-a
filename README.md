# Azure SRE Agent repo

Comprehensive SRE operations automation using Azure SRE Agent with Model Context Protocol (MCP) integration.

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

**[BLOG_POST](https://techcommunity.microsoft.com/blog/appsonazureblog/mcp-driven-azure-sre-for-databricks/4494630)** — MCP-Driven Azure SRE for Databricks
- Proactive compliance automation with best practice validation
- Reactive incident response with root cause analysis
- Real-world examples and operational impact metrics

---


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
**Built for SRE teams automating Azure operations with intelligence and speed.**
