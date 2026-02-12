# Databricks MCP to Azure Container Apps - Deployment from Local Src

**Date**: February 9, 2026  
**Status**: ✅ **SUCCESSFULLY DEPLOYED AND TESTED**  
**Approach**: Build from local `src/` folder (databricks-mcp v0.4.4)  
**Target**: Azure Container Apps with streamable HTTP transport  
**Registry**: aks01day2acr.azurecr.io  
**Resource Group**: aks01day2-rg  
**Region**: centralus

**Live Endpoint**: `https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp`  
**Container Image**: `aks01day2acr.azurecr.io/databricks-mcp:final` (digest: `sha256:bebce83...`)  
**Container App Revision**: `databricks-mcp--0000004`

---

## Quick Summary

This guide deploys the Databricks MCP server from the local `src/` folder to Azure Container Apps (ACA). The deployment includes:

*   ✅ FastMCP with streamable HTTP transport
*   ✅ 38 Databricks tools (clusters, jobs, SQL, Unity Catalog, notebooks, repos, libraries)
*   ✅ Managed Identity for secure ACR access
*   ✅ Environment-based secrets management
*   ✅ Reverse proxy support (DNS rebinding protection disabled for ACA)
*   ✅ Ready for Azure SRE Agent integration

**Estimated Time**: 45 minutes  
**Effort Level**: Intermediate

---

## Key Technical Fixes Applied

This deployment includes critical fixes discovered during development:

### 1\. Host Binding Issue (0.0.0.0)

**Problem**: FastMCP binds to `127.0.0.1` by default, making it inaccessible from Docker/ACA networks.  
**Solution**: Override in `entry_http.py`:

```python
server.settings.host = "0.0.0.0"
server.settings.port = 8000
```

### 2\. DNS Rebinding Protection (ACA Proxy Headers)

**Problem**: Azure Container Apps ingress modifies Host headers, triggering MCP's security middleware.  
**Solution**: Disable DNS rebinding protection in `entry_http.py`:

```python
server.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False
)
```

This is safe because ACA provides infrastructure-level isolation.

### 3\. Virtual Environment Isolation

**Problem**: Using `uv pip install --system` mixes dependencies with system Python.  
**Solution**: Use `uv venv && uv pip install .` to create isolated `.venv/` directory.

### 4\. Dockerfile Template Alignment

**Applied**: Matching Azure reference implementation pattern (uv + venv + proper CMD).

---

## Prerequisites Checklist

*   ✅ Local src folder validated at: `C:\Users\varghesejoji\Desktop\SRE-A\zDatabricksMCP\src`
*   ✅ Pre-Docker validation completed (all 38 tools working via streamable HTTP)
*   ✅ Docker Desktop running
*   Azure CLI logged in (`az login`)
*   Existing ACR: `aks01day2acr.azurecr.io`
*   Databricks credentials ready:
    *   DATABRICKS\_HOST: `https://<DATABRICKS_HOST>`
  *   DATABRICKS\_TOKEN: `<DATABRICKS_TOKEN>` (⚠️ rotate post-deployment)
    *   DATABRICKS\_WAREHOUSE\_ID: `<DATABRICKS_WAREHOUSE_ID>`

---

## Architecture Overview

```
Local Src Folder (databricks-mcp v0.4.4)
    ↓
Docker Build (copies src/ → /app, installs with uv)
    ↓
Docker Image (databricks-mcp:0.4.4-src)
    ↓
Azure Container Registry (aks01day2acr.azurecr.io/databricks-mcp:0.4.4-src)
    ↓
Azure Container Apps (with Managed Identity + Secrets)
    ↓
Public HTTPS Endpoint (for Azure SRE Agent integration)
```

---

## Step 1: Verify Src Folder Structure

### 1.1 Check Src Contents

```
ls C:\Users\varghesejoji\Desktop\SRE-A\zDatabricksMCP\src
```

**Expected Files/Folders:**

```
databricks_mcp/       (main package directory)
pyproject.toml        (package configuration with dependencies)
README.md             (documentation)
.venv/                (virtual environment - NOT copied to Docker)
tests/                (test files)
.env.example          (environment variable template)
```

### 1.2 Verify pyproject.toml Entry Points

```
cat C:\Users\varghesejoji\Desktop\SRE-A\zDatabricksMCP\src\pyproject.toml | Select-String "scripts"
```

**Expected Output:**

```
[project.scripts]
databricks-mcp-server = "databricks_mcp.server.databricks_mcp_server:main"
```

---

## Step 2: Build Docker Image from Src

### 2.1 Navigate to Src Directory

```
cd C:\Users\varghesejoji\Desktop\SRE-A\zDatabricksMCP\src
```

**Important**: The Dockerfile is now in the `src/` folder itself.

### 2.2 Build the Docker Image

```
docker build -q -t databricks-mcp:final .
```

**Build Process:**

1.  Uses `python:3.13-slim` base image
2.  Copies `uv` from `ghcr.io/astral-sh/uv:latest`
3.  Copies entire directory → `/app/`
4.  Creates virtual environment: `uv venv`
5.  Installs dependencies: `uv pip install .`
6.  Sets CMD: `python /app/entry_http.py`

**Expected Output:**

```
sha256:fbd67ce60ae97ef69cfc1fe59e8f3f331e05752d6441c53e0f20a063e50a5ee1
```

### 2.3 Verify Image Creation

```
docker images | Select-String "databricks-mcp"
```

**Expected Output:**

```
databricks-mcp   final   fbd67ce60ae97   2 minutes ago   485MB
```

---

## Step 3: Test Docker Image Locally

### 3.1 Run Container Locally

```
docker run -d --name databricks-mcp-test `
  -p 8000:8000 `
  -e DATABRICKS_HOST="https://<DATABRICKS_HOST>" `
  -e DATABRICKS_TOKEN="<DATABRICKS_TOKEN>" `
  -e DATABRICKS_WAREHOUSE_ID="<DATABRICKS_WAREHOUSE_ID>" `
  -e LOG_LEVEL="INFO" `
  databricks-mcp:0.4.4-src
```

### 3.2 Check Container Logs

```
# Wait 5 seconds for startup
Start-Sleep -Seconds 5

# View logs
docker logs databricks-mcp-test
```

**Expected Output (JSON logs):**

```
{"name": "databricks_mcp.server.databricks_mcp_server", "level": "INFO", "message": "Starting Databricks MCP server", "timestamp": "2026-02-09T20:45:12-0500"}
{"name": "databricks_mcp.server.databricks_mcp_server", "level": "INFO", "message": "Initializing Databricks MCP server", "timestamp": "2026-02-09T20:45:13-0500"}
{"name": "mcp.server.fastmcp", "level": "INFO", "message": "Server listening on port 8000 with transport streamable-http"}
```

### 3.3 Test MCP Session Management

```
# Initialize session
$initPayload = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2024-11-05"
        capabilities = @{}
        clientInfo = @{
            name = "docker-test"
            version = "1.0.0"
        }
    }
} | ConvertTo-Json -Depth 10

$init = Invoke-WebRequest -Uri "http://localhost:8000/mcp" -Method POST -Body $initPayload -ContentType "application/json"
$sessionId = ($init.Headers["Mcp-Session-Id"] -join "")
Write-Host "✅ Session ID: $sessionId"

# List tools
$toolsPayload = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/list"
    params = @{}
} | ConvertTo-Json -Depth 10

$headers = @{
    "Content-Type" = "application/json"
    "Mcp-Session-Id" = $sessionId
}

$tools = Invoke-RestMethod -Uri "http://localhost:8000/mcp" -Method POST -Body $toolsPayload -Headers $headers
Write-Host "✅ Available tools: $($tools.result.tools.Count)"
$tools.result.tools | Select-Object -First 5 | ForEach-Object { Write-Host "   - $($_.name)" }
```

**Expected Output:**

```
✅ Session ID: 550e8400-e29b-41d4-a716-446655440000
✅ Available tools: 38
   - list_clusters
   - create_cluster
   - terminate_cluster
   - get_cluster
   - start_cluster
```

### 3.4 Test a Real Tool (list\_catalogs)

```
$catalogsPayload = @{
    jsonrpc = "2.0"
    id = 3
    method = "tools/call"
    params = @{
        name = "list_catalogs"
        arguments = @{}
    }
} | ConvertTo-Json -Depth 10

$catalogs = Invoke-RestMethod -Uri "http://localhost:8000/mcp" -Method POST -Body $catalogsPayload -Headers $headers
Write-Host "✅ Catalogs found: $($catalogs.result.content[0].text)"
```

**Expected Output:**

```
✅ Catalogs found: Found 3 catalogs
```

### 3.5 Clean Up Test Container

```
docker stop databricks-mcp-test
docker rm databricks-mcp-test
```

---

## Step 4: Push to Azure Container Registry

### 4.1 Login to ACR

```
az acr login --name aks01day2acr
```

**Expected Output:**

```
Login Succeeded
```

### 4.2 Tag Image for ACR

```
docker tag databricks-mcp:final aks01day2acr.azurecr.io/databricks-mcp:final
```

### 4.3 Push to ACR

```
docker push aks01day2acr.azurecr.io/databricks-mcp:final
```

**Expected Output:**

```
The push refers to repository [aks01day2acr.azurecr.io/databricks-mcp]
7218afb76b65: Pushed
1c0ef9ea650d: Pushed
b58a27b34e67: Pushed
final: digest: sha256:bebce83051bfe8d24324ff3f9372836bd38e89327a7bfee61d304c0febc0f1e3 size: 2208
```

### 4.4 Verify Image in ACR

```
az acr repository show --name aks01day2acr --repository databricks-mcp
```

---

## Step 5: Create Managed Identity

### 5.1 Create Identity

```
az identity create `
  --name databricks-mcp-identity `
  --resource-group aks01day2-rg `
  --location centralus
```

### 5.2 Get Identity Principal ID and Client ID

```
$identityId = az identity show --name databricks-mcp-identity --resource-group aks01day2-rg --query id -o tsv
$principalId = az identity show --name databricks-mcp-identity --resource-group aks01day2-rg --query principalId -o tsv
$clientId = az identity show --name databricks-mcp-identity --resource-group aks01day2-rg --query clientId -o tsv

Write-Host "Identity ID: $identityId"
Write-Host "Principal ID: $principalId"
Write-Host "Client ID: $clientId"
```

### 5.3 Grant ACR Pull Permission

```
$acrId = az acr show --name aks01day2acr --query id -o tsv

az role assignment create `
  --assignee $principalId `
  --role AcrPull `
  --scope $acrId
```

**Expected Output:**

```
{
  "principalId": "...",
  "principalType": "ServicePrincipal",
  "roleDefinitionName": "AcrPull",
  "scope": "/subscriptions/.../resourceGroups/aks01day2-rg/providers/Microsoft.ContainerRegistry/registries/aks01day2acr"
}
```

---

## Step 6: Create Azure Container Apps Environment

### 6.1 Create Environment

```
az containerapp env create `
  --name databricks-mcp-env `
  --resource-group aks01day2-rg `
  --location centralus
```

**Expected Output:**

```
Creating Container Apps Environment... (this may take several minutes)
```

### 6.2 Verify Environment

```
az containerapp env show `
  --name databricks-mcp-env `
  --resource-group aks01day2-rg `
  --query "provisioningState"
```

**Expected Output:**

```
"Succeeded"
```

---

## Step 7: Deploy Container App

### 7.1 Create Container App with Secrets

```
az containerapp create `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --environment databricks-mcp-env `
  --image aks01day2acr.azurecr.io/databricks-mcp:final `
  --registry-server aks01day2acr.azurecr.io `
  --registry-identity $identityId `
  --user-assigned $identityId `
  --target-port 8000 `
  --ingress external `
  --min-replicas 1 `
  --max-replicas 3 `
  --cpu 0.5 `
  --memory 1.0Gi `
  --secrets `
    databricks-token="<DATABRICKS_TOKEN>" `
  --env-vars `
    DATABRICKS_HOST="https://<DATABRICKS_HOST>" `
    DATABRICKS_TOKEN=secretref:databricks-token `
    DATABRICKS_WAREHOUSE_ID="<DATABRICKS_WAREHOUSE_ID>" `
    LOG_LEVEL="INFO"
```

**Expected Output:**

```
Container app created. Access your app at https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/
```

### 7.2 Get Container App FQDN

```
$fqdn = az containerapp show `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "🌐 Container App URL: https://$fqdn"
Write-Host "🔗 MCP Endpoint: https://$fqdn/mcp"
```

**Output:**

```
🌐 Container App URL: https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io
🔗 MCP Endpoint: https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp
```

---

## Step 8: Validate Deployment

### 8.1 Check Container App Status

```
az containerapp show `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --query "{name:name, provisioningState:properties.provisioningState, runningStatus:properties.runningStatus, fqdn:properties.configuration.ingress.fqdn}"
```

**Expected Output:**

```
{
  "fqdn": "databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io",
  "name": "databricks-mcp",
  "provisioningState": "Succeeded",
  "runningStatus": "Running"
}
```

### 8.2 Test Remote MCP Endpoint

```
$fqdn = az containerapp show --name databricks-mcp --resource-group aks01day2-rg --query "properties.configuration.ingress.fqdn" -o tsv

# Initialize session
$initPayload = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2024-11-05"
        capabilities = @{}
        clientInfo = @{
            name = "azure-test"
            version = "1.0.0"
        }
    }
} | ConvertTo-Json -Depth 10

$init = Invoke-WebRequest -Uri "https://$fqdn/mcp" -Method POST -Body $initPayload -ContentType "application/json"
$sessionId = ($init.Headers["Mcp-Session-Id"] -join "")
Write-Host "✅ Remote Session ID: $sessionId"

# List tools
$toolsPayload = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/list"
    params = @{}
} | ConvertTo-Json -Depth 10

$headers = @{
    "Content-Type" = "application/json"
    "Mcp-Session-Id" = $sessionId
}

$tools = Invoke-RestMethod -Uri "https://$fqdn/mcp" -Method POST -Body $toolsPayload -Headers $headers
Write-Host "✅ Remote tools available: $($tools.result.tools.Count)"
```

**Actual Validated Output:**

```
✅ Remote Session ID: 2921023b31684282b7d58ee18295e70e
✅ Remote tools available: 38
```

### 8.3 Run Validation Tests

Three validation test scripts are included in the repository:

#### Test 1: Natural Language Test

```
python test_natural_language.py
```

Demonstrates conversational AI interactions with Databricks via MCP. Shows how natural language prompts are translated to MCP tool calls.

**Sample Output:**

```
💬 You: What compute clusters do I have running right now?
🔧 [MCP translates to: list_clusters({})]
🤖 Databricks: Found 0 clusters

💬 You: Run this SQL query for me: SELECT current_timestamp() as now, current_user() as user
🔧 [MCP translates to: execute_sql(...)]
🤖 Databricks: SQL statement 01f1062d-d407-166a-9e9b-d8c0acd5a897 executed
```

#### Test 2: Comprehensive MCP Test Suite

```
python test_mcp_databricks.py
```

Runs 5 structured validation tests covering key MCP operations. Tests include error handling and work with both JSON and plain text responses.

**Expected Result:**

```
✅ All tests completed successfully!
Session ID: 7a236406dde542e8b8e12fe9d3349b07
Total requests: 7
```

#### Test 3: Tool Discovery

```
python discover_tools.py
```

Lists all 38 available MCP tools with descriptions.

**Expected Result:**

```
✅ Found 38 tools:
  • list_clusters - List all Databricks clusters
  • create_cluster - Create a new Databricks cluster
  • terminate_cluster - Terminate a cluster
  ... (35 more tools)
```

See [TEST-README.md](TEST-README.md) for detailed test documentation.

### 8.4 View Container Logs

```
az containerapp logs show `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --tail 50
```

**Expected Log Output:**

```
{"name": "databricks_mcp.server.databricks_mcp_server", "level": "INFO", "message": "Initializing Databricks MCP server", "timestamp": "2026-02-10T02:54:38+0000"}
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
{"name": "mcp.server.streamable_http_manager", "level": "INFO", "message": "StreamableHTTP session manager started", "timestamp": "2026-02-10T02:54:38+0000"}
```

---

## Step 9: Azure SRE Agent Integration

### 9.1 Get MCP Server URL

```
$fqdn = "databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io"
Write-Host "MCP Server URL: https://$fqdn/mcp"
```

**Output:**

```
MCP Server URL: https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp
```

### 9.2 Azure SRE Agent Connector Setup (UI)

If your Azure SRE Agent has a UI-based MCP connector configuration, use these settings:

**Configuration Form:**

| Setting | Value |
|---------|-------|
| **Name** | `DbxMCP` |
| **Connection type** | `Streamable-HTTP` ✓ |
| **URL** | `https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp` |
| **Authentication method** | `Custom headers` |

**⚠️ CRITICAL - Add this custom header:**

| Header Key | Header Value |
|------------|--------------|
| `Accept` | `application/json, text/event-stream` |

**Why this header is required:**  
The MCP streamable-http transport requires clients to accept both JSON responses and Server-Sent Events (SSE). Without this header, you'll get a `400 Bad Request` error.

**Expected Result:**
- ✅ Connection status: Connected
- ✅ Tools: 38
- ✅ Last heartbeat: Current timestamp
- ✅ No errors

**Common Issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` | Missing Accept header | Add `Accept: application/json, text/event-stream` |
| `404 Not Found` | Missing `/mcp` path | Ensure URL ends with `/mcp` |
| `Connection timeout` | Wrong URL/FQDN | Verify Container App FQDN |

**Verify Connection:**

```powershell
# Test the endpoint manually
$url = "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp"
$headers = @{
    "Accept" = "application/json, text/event-stream"
    "Content-Type" = "application/json"
}
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2024-11-05"
        capabilities = @{}
        clientInfo = @{
            name = "test"
            version = "1.0"
        }
    }
} | ConvertTo-Json -Compress

$response = Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body $body -UseBasicParsing
Write-Host "Status: $($response.StatusCode)"
$response.Content
```

**Expected Output:**
```
Status: 200
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",...}}
```

### 9.3 Configure Azure SRE Agent (JSON Config)

If using JSON configuration file (e.g., `subagent.yaml` or agent settings):

```json
{
  "mcp_servers": {
    "databricks-mcp": {
      "url": "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp",
      "transport": "streamable-http",
      "description": "Databricks MCP Server for workspace management",
      "headers": {
        "Accept": "application/json, text/event-stream"
      }
    }
  }
}
```

### 9.4 Test from SRE Agent

In the SRE Agent prompt:

```
List all Databricks catalogs using the Databricks MCP server
```

Expected agent behavior:

1.  Connects to `https://<fqdn>/mcp`
2.  Initializes MCP session
3.  Calls `list_catalogs` tool
4.  Returns catalog list

---

## Step 10: Monitoring and Maintenance

### 10.1 Check Container App Metrics

```
az monitor metrics list `
  --resource $(az containerapp show --name databricks-mcp --resource-group aks01day2-rg --query id -o tsv) `
  --metric "Requests" `
  --start-time (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
```

### 10.2 View Real-Time Logs

```
az containerapp logs show `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --follow
```

### 10.3 Scale Container App

```
az containerapp update `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --min-replicas 2 `
  --max-replicas 5
```

### 10.4 Update Databricks Token (Rotate)

```
# Update secret
az containerapp update `
  --name databricks-mcp `
  --resource-group aks01day2-rg `
  --set-env-vars DATABRICKS_TOKEN=secretref:databricks-token `
  --replace-secrets databricks-token="<new-token>"

# Restart to apply
az containerapp revision restart `
  --name databricks-mcp `
  --resource-group aks01day2-rg
```

---

## Step 11: Troubleshooting

### 11.1 Container Won't Start

```
# Check logs for errors
az containerapp logs show --name databricks-mcp --resource-group aks01day2-rg --tail 100

# Common issues:
# - Missing environment variables (check secrets)
# - Invalid Databricks credentials (test manually)
# - Port mapping issues (ensure 8000 is exposed)
```

### 11.2 MCP Session Failures

```
# Test endpoint health
Invoke-WebRequest -Uri "https://$fqdn/health" -Method GET

# Re-initialize session
$init = Invoke-WebRequest -Uri "https://$fqdn/mcp" -Method POST -Body $initPayload -ContentType "application/json"
```

### 11.3 ACR Pull Failures

```
# Verify managed identity has AcrPull role
az role assignment list --assignee $principalId --scope $acrId

# Re-assign if missing
az role assignment create --assignee $principalId --role AcrPull --scope $acrId
```

---

## Step 12: Clean Up (If Needed)

```
# Delete container app
az containerapp delete --name databricks-mcp --resource-group aks01day2-rg --yes

# Delete environment
az containerapp env delete --name databricks-mcp-env --resource-group aks01day2-rg --yes

# Delete managed identity
az identity delete --name databricks-mcp-identity --resource-group aks01day2-rg

# Delete image from ACR
az acr repository delete --name aks01day2acr --repository databricks-mcp --yes
```

---

## Appendix: Complete Testing Guide

### Available MCP Tools (38 Total)

All tools are available via the streamable HTTP endpoint after initialization with an MCP session.

**Cluster Management (5 tools)**
- `list_clusters` - List all Databricks clusters
- `create_cluster` - Create a new cluster
- `terminate_cluster` - Terminate a cluster
- `get_cluster` - Get cluster information
- `start_cluster` - Start a terminated cluster

**Job Management (8 tools)**
- `list_jobs` - List Databricks jobs
- `create_job` - Create a new job
- `delete_job` - Delete a job
- `run_job` - Trigger a job run
- `run_notebook` - Submit a one-time notebook run
- `get_run_status` - Get job run status
- `list_job_runs` - List recent job runs
- `cancel_run` - Cancel a job run

**Notebooks & Workspace (6 tools)**
- `list_notebooks` - List notebooks in a directory
- `export_notebook` - Export a notebook
- `import_notebook` - Import a notebook
- `delete_workspace_object` - Delete notebook or directory
- `get_workspace_file_content` - Get file content
- `get_workspace_file_info` - Get file metadata

**DBFS Operations (3 tools)**
- `list_files` - List DBFS files
- `dbfs_put` - Upload content to DBFS
- `dbfs_delete` - Delete DBFS path

**Library Management (3 tools)**
- `install_library` - Install libraries on cluster
- `uninstall_library` - Uninstall libraries
- `list_cluster_libraries` - List cluster libraries

**Repos & Git Integration (4 tools)**
- `create_repo` - Create or clone a repo
- `update_repo` - Update repo branch/tag
- `list_repos` - List workspace repos
- `pull_repo` - Pull latest commit

**SQL & Unity Catalog (8 tools)**
- `execute_sql` - Execute SQL statement
- `list_catalogs` - List Unity Catalog catalogs
- `create_catalog` - Create a catalog
- `list_schemas` - List schemas in catalog
- `create_schema` - Create a schema
- `list_tables` - List tables in schema
- `create_table` - Create table via SQL
- `get_table_lineage` - Get table lineage

### Test Files & Validation Scripts

Three validation test scripts are provided:

#### 1. Natural Language Test (`test_natural_language.py`)

Demonstrates human-friendly interactions with Databricks via MCP using natural language prompts.

**Features:**
- Simulates conversational AI interface
- Translates natural language to MCP tool calls
- Human-readable responses
- Shows session management

**Usage:**
```bash
python test_natural_language.py
```

**Example Output:**
```
💬 You: What compute clusters do I have running right now?
🔧 [MCP translates to: list_clusters({})]
🤖 Databricks: Found 0 clusters

💬 You: Run this SQL query for me: SELECT current_timestamp() as now, current_user() as user
🔧 [MCP translates to: execute_sql(...)]
🤖 Databricks: SQL statement 01f1062d-d407-166a-9e9b-d8c0acd5a897 executed

✅ Conversation completed successfully!
   Total interactions: 6
   Session ID: a2b88a212f5c4fb58f8350222cfd8eba
```

#### 2. Comprehensive MCP Test Suite (`test_mcp_databricks.py`)

Structured validation test with multiple Databricks operations.

**Test Coverage:**
- TEST 1: List clusters
- TEST 2: List SQL warehouses
- TEST 3: List Unity Catalog catalogs
- TEST 4: Execute SQL query
- TEST 5: List jobs

**Usage:**
```bash
python test_mcp_databricks.py
```

**Expected Output:**
```
✅ All tests completed successfully!
Session ID: 7a236406dde542e8b8e12fe9d3349b07
Total requests: 7
```

#### 3. Tool Discovery (`discover_tools.py`)

Quick script to list all available MCP tools and their descriptions.

**Usage:**
```bash
python discover_tools.py
```

**Expected Output:**
```
✅ Found 38 tools:
  • list_clusters - List all Databricks clusters
  • create_cluster - Create a new Databricks cluster
  • terminate_cluster - Terminate a cluster
  • ... (35 more tools)
```

### MCP Protocol Reference

#### Request Format (JSON-RPC 2.0)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_clusters",
    "arguments": {}
  }
}
```

#### Response Format (Server-Sent Events)

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}
```

#### Required Headers

```
Content-Type: application/json
Accept: application/json, text/event-stream
Mcp-Session-Id: <session-id-from-initialize>
```

### Configuration & Prerequisites

**Python Requirements:**
```bash
pip install requests
```

**Endpoint Configuration:**
```python
base_url = "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io"
warehouse_id = "<DATABRICKS_WAREHOUSE_ID>"  # Your SQL warehouse ID
```

**Endpoint Information:**
- **Base URL**: `https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io`
- **MCP Endpoint**: `/mcp`
- **Transport**: Streamable HTTP (SSE)
- **Protocol**: MCP 2024-11-05

### Troubleshooting Tests

#### Connection Errors

**Symptom:** Cannot connect to the MCP endpoint

**Troubleshooting:**
```bash
# Verify endpoint is accessible
curl -I https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io

# Check Azure Container App status
az containerapp show --name databricks-mcp --resource-group aks01day2-rg --query "properties.runningStatus"

# View real-time logs
az containerapp logs show --name databricks-mcp --resource-group aks01day2-rg --follow
```

**Common Issues:**
- Endpoint URL is incorrect
- Network connectivity problem
- Azure Container Apps service is stopped/unavailable
- Firewall blocking HTTPS port 443

#### Authentication Errors

**Symptom:** "Invalid Host header" or "Unauthorized"

**Details:**
- Databricks PAT token is configured as a secret in ACA
- MCP server handles Databricks authentication internally
- Verify environment variables are set in Container App

**Troubleshooting:**
```bash
# Check environment variables
az containerapp show --name databricks-mcp --resource-group aks01day2-rg --query "properties.template.containers[0].env"

# Verify secrets exist
az containerapp secret list --name databricks-mcp --resource-group aks01day2-rg
```

#### Tool Errors

**Symptom:** Tool call fails with "Unknown tool" or parameter validation error

**Troubleshooting:**
```bash
# List available tools
python discover_tools.py

# Verify tool parameter names
python discover_tools.py | grep "list_catalogs"

# Check Databricks resource names (catalogs, schemas exist)
python test_natural_language.py
```

**Common Issues:**
- Incorrect tool name (use discover_tools.py to find exact names)
- Wrong parameter names (e.g., `query` vs `statement` for SQL)
- Databricks resources don't exist (catalog, schema, table names)
- Insufficient permissions in Databricks workspace

### Complete Example: Full MCP Workflow

```python
import requests
import json

# 1. Initialize session
init_response = requests.post(
    "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    },
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "my-client", "version": "1.0"}
        }
    }
)

session_id = init_response.headers["Mcp-Session-Id"]
print(f"Session ID: {session_id}")

# 2. List available tools
tools_response = requests.post(
    "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session_id
    },
    json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
)

# 3. Call a tool
call_response = requests.post(
    "https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session_id
    },
    json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_catalogs",
            "arguments": {}
        }
    }
)

# 4. Parse SSE response
content = call_response.text
for line in content.split('\n'):
    if line.startswith('data: '):
        result = json.loads(line[6:])
        print("Catalog Response:")
        print(json.dumps(result, indent=2))
        break
```

**Expected Output:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 3 catalogs"
      }
    ]
  }
}
```

---

## Validation Tests

After deployment, use these test scripts to validate the MCP server:

### 1\. Natural Language Test

```
python test_natural_language.py
```

Simulates conversational AI interactions with Databricks via MCP:

```
💬 You: What compute clusters do I have running right now?
🔧 [MCP translates to: list_clusters({})]
🤖 Databricks: Found 0 clusters
```

### 2\. Comprehensive MCP Test Suite

```
python test_mcp_databricks.py
```

Runs 5 validation tests:

*   TEST 1: List clusters
*   TEST 2: List SQL warehouses
*   TEST 3: List Unity catalogs
*   TEST 4: Execute SQL query
*   TEST 5: List jobs

### 3\. Tool Discovery

```
python discover_tools.py
```

Lists all 38 available MCP tools with descriptions.

All tests are located in `zDatabricksMCP/` directory.

---

*   ⚠️ **CRITICAL**: Rotate Databricks PAT token (currently exposed in chat history)
*   Configure Azure Key Vault for secrets management
*   Enable Container App authentication/authorization
*   Set up Azure Monitor alerts for failures
*   Configure log retention policies
*   Review managed identity permissions (least privilege)
*   Enable HTTPS only (external ingress default)
*   Document MCP endpoint URL for team

---

## Summary

**✅ DEPLOYMENT STATUS**: COMPLETE AND VALIDATED

**Live Deployment:**

*   **Container App**: `databricks-mcp`
*   **Endpoint**: `https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp`
*   **Status**: ✅ Running
*   **Revision**: `databricks-mcp--0000004`
*   **Image**: `aks01day2acr.azurecr.io/databricks-mcp:final` (digest: `sha256:bebce83...`)
*   **Tools Available**: 38
*   **Session Management**: ✅ Working
*   **DNS Rebinding Protection**: ✅ Disabled (for ACA proxy)

**Key Files Created:**

*   `src/Dockerfile` - Multi-stage Docker build with uv venv isolation
*   `src/entry_http.py` - MCP entry point with 0.0.0.0 binding and proxy support
*   `DEPLOYMENT_STEPS_SRC.md` - Complete deployment guide with integrated testing reference (this file)
*   `test_natural_language.py` - Conversational AI test
*   `test_mcp_databricks.py` - Comprehensive MCP test suite
*   `discover_tools.py` - Tool discovery utility

**Validation Results:**

*   ✅ Local Docker image builds successfully
*   ✅ Local Docker container runs with full tool access
*   ✅ Azure Container Registry image push successful
*   ✅ Azure Container Apps deployment successful
*   ✅ Remote MCP endpoint responds with session ID
*   ✅ All 38 tools available via remote endpoint
*   ✅ Natural language test running successfully
*   ✅ MCP test suite passing all 5 tests
*   ✅ Tool discovery working correctly

**Quick Access URLs:**

```
MCP Endpoint:        https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io/mcp
Container App:       https://databricks-mcp.icysand-20762073.centralus.azurecontainerapps.io
Databricks Workspace: https://<DATABRICKS_HOST>
```

**Configured Resources:**

*   Resource Group: `aks01day2-rg`
*   Container App Environment: `databricks-mcp-env`
*   Managed Identity: `databricks-mcp-identity`
*   Registry: `aks01day2acr.azurecr.io`
*   CPU: 0.5 cores, Memory: 1.0 Gi
*   Min Replicas: 1, Max Replicas: 3

**Next Steps:**

1.  Run validation tests: `python test_natural_language.py`
2.  Integrate with Azure SRE Agent (see Step 9)
3.  Rotate Databricks PAT token (⚠️ CRITICAL - see Security Checklist)
4.  Monitor deployment via Azure Monitor
5.  Set up log analytics and alerts

**For Reference:**

*   See [TEST-README.md](TEST-README.md) for detailed test documentation
*   See [azure.instructions.md](../zDatabricksMCP/) for Azure best practices
*   See src/entry\_http.py for technical implementation details

---

## Deployment Complete! 🎉

The Databricks MCP server is now live on Azure Container Apps and ready for integration with the Azure SRE Agent.

**To verify the deployment is working:**

```
python test_natural_language.py
```

**To use with Azure SRE Agent:**  
Configure the MCP connector using Step 9.2 (UI) or Step 9.3 (JSON config) with the required Accept header.