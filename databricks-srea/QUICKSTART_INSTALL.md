# Databricks MCP - Quickstart Installation Guide

**Target**: Containerize and deploy Databricks MCP to Azure Container Apps, then test locally.  
**Time**: 30-40 minutes  
**Difficulty**: Beginner-Intermediate

---

## Table of Contents

*   [Deployment Overview](#deployment-overview)
*   [Prerequisites](#prerequisites)
*   [Validation Complete](#-validation-complete-steps-2-8)
*   [Step 1: Create Managed Identity (Required)](#step-1-create-managed-identity-required)
*   [Step 2: Prepare Local Source](#step-2-prepare-local-source)
*   [Step 3: Build Docker Image Locally](#step-3-build-docker-image-locally)
*   [Step 4: Test Locally with Docker](#step-4-test-locally-with-docker)
*   [Step 5: Push to Azure Container Registry](#step-5-push-to-azure-container-registry)
*   [Step 6: Deploy to Azure Container Apps](#step-6-deploy-to-azure-container-apps)
*   [Step 7: Test Remote Endpoint](#step-7-test-remote-endpoint)
*   [Step 8: Test MCP Tools](#step-8-test-mcp-tools)
*   [Step 9: Verification Checklist](#step-9-verification-checklist)
*   [Step 10: Configure for SRE Agent Integration](#step-10-configure-for-sre-agent-integration)
*   [Step 11: Create Subagent in Azure SRE Agent UI](#step-11-create-subagent-in-azure-sre-agent-ui)
*   [Troubleshooting](#troubleshooting)
*   [Reference](#reference)

---

## Deployment Overview

This guide walks you through a complete end-to-end deployment of the Databricks MCP server, from local development to production Azure infrastructure. Understanding the architecture before you begin will help you troubleshoot issues and make informed decisions during deployment.

### What You're Building

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure SRE Agent                             │
│              (Orchestrates SRE workflows)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS + MCP Protocol
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Azure Container Apps (Production Runtime)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   Databricks MCP Container                                │  │
│  │   - HTTP Server (Port 8000)                               │  │
│  │   - MCP Protocol Handler (/mcp endpoint)                  │  │
│  │   - 38 Databricks Tools (clusters, jobs, SQL, Unity)      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          │ Pulls image via Managed Identity      │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   Azure Container Registry (ACR)                          │  │
│  │   - Stores databricks-mcp:latest and :final images        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Databricks REST APIs
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Databricks Workspace                          │
│   - Clusters, Jobs, Notebooks, Unity Catalog, SQL Warehouses    │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Pipeline

**Local Development & Testing (Steps 2-4)**  
Build and test the Docker container on your machine to validate functionality before cloud deployment. This catches configuration issues early and lets you iterate quickly.

**Azure Container Registry (Step 5)**  
Push the validated Docker image to ACR, Azure's private container registry. This acts as your production image repository with enterprise-grade security and geo-replication.

**Azure Container Apps Deployment (Step 6)**  
Deploy the MCP server as a managed container with automatic scaling, health monitoring, and HTTPS ingress. Container Apps handles infrastructure management (patching, scaling, networking) so you focus on the MCP logic.

**Authentication & Security (Step 1 + 6)**  
Managed Identity eliminates credential storage by granting the Container App permission to pull images from ACR and the MCP server permission to call Databricks APIs.

**Validation & Integration (Steps 7-11)**  
Test the live endpoint, validate MCP protocol responses, and connect the Azure SRE Agent to orchestrate Databricks operations through natural language prompts.

### Key Components

**Databricks MCP Server**: Python application (`entry_http.py`) that exposes Databricks workspace operations as MCP tools. Runs as HTTP server on port 8000 with `/mcp` endpoint handling JSON-RPC 2.0 requests.

**Azure Container Registry (ACR)**: Private Docker registry storing your MCP container images with role-based access control and vulnerability scanning.

**Azure Container Apps**: Serverless container platform hosting the MCP server with built-in scaling (0-N replicas), managed certificates, and environment variable/secret injection.

**Managed Identity**: Azure AD identity assigned to Container App enabling passwordless authentication to ACR (image pull) and Databricks workspace (API access).

**Azure SRE Agent**: AI-powered operations assistant that discovers and calls MCP tools to execute complex Databricks workflows autonomously.

### Why This Architecture?

**Containerization**: Packages Python dependencies, MCP server code, and runtime into a single immutable artifact that works identically in development and production.

**Azure Container Apps**: Eliminates Kubernetes complexity while providing enterprise container orchestration (scaling, health checks, secrets management, ingress).

**Managed Identity**: Replaces service principal credentials with Azure AD-managed identities that auto-rotate and never expire, eliminating credential sprawl.

**MCP Protocol**: Standardized interface for AI agents to discover and invoke tools, enabling the SRE Agent to orchestrate Databricks operations without custom integration code.

### What Happens at Runtime?

1. Azure SRE Agent receives user prompt: "List all Databricks clusters with high memory usage"
2. Agent calls `https://<container-app-url>/mcp` with MCP `initialize` request
3. Container App authenticates via Managed Identity and returns list of 38 available tools
4. Agent selects `list_clusters` tool and invokes it via MCP `tools/call` request
5. MCP server calls Databricks REST API using workspace token (stored as Container App secret)
6. Databricks returns cluster list, MCP server filters by memory usage, responds to agent
7. Agent formats findings and presents actionable insights to user

---

## Prerequisites

Before starting, verify you have:

*   ✅ Docker Desktop installed and running
*   ✅ Azure CLI installed (`az --version`)
*   ✅ Logged into Azure: `az login`
*   ✅ PowerShell or bash terminal
*   ✅ Python 3.9+ installed (for local testing)
*   ✅ Git clone/local copy of `src/` folder with `entry_http.py` and `pyproject.toml`

### Azure Resources Required

*   ✅ Azure Container Registry (ACR) - note the URL (e.g., `myacr.azurecr.io`)
*   ✅ Azure Container Apps Environment
*   ✅ Resource Group
*   ✅ **Managed Identity** - for secure ACR access (created in Step 1.1)

### Databricks Credentials

Gather these before proceeding:

```
DATABRICKS_HOST=https://adb-xxxxxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi...
DATABRICKS_WAREHOUSE_ID=xxxxx
```

⚠️ Keep the token secure—rotate after deployment.

---

## ✅ VALIDATION COMPLETE (Steps 2-8)

The following steps have been validated:

*   ✅ **Step 2**: Source code structure verified - all required files present
*   ✅ **Step 3**: Docker image builds successfully (246MB, ~5-10 min first build)
*   ✅ **Step 4**: Container starts and MCP endpoint responds to protocol requests
*   Server binds to `0.0.0.0:8000` correctly
*   MCP initialize request returns valid protocol response
*   Protocol version: `2024-11-05` compatible
*   ✅ **Step 5**: Docker image successfully pushed to ACR
*   Tags: `latest` and `final` available in ACR
*   Image digest: sha256:0ef5c9618bb9
*   ✅ **Step 6**: Container App deployed and reachable
*   ✅ **Step 7**: Remote MCP initialize request succeeded (HTTP 200)
*   ✅ **Step 8**: Tools list and validation run succeeded
*   Warehouse listing tool not advertised in this build

---

## Step 1: Create Managed Identity (Required)

### 1.1 Create Identity

The Container App needs a **Managed Identity** to authenticate to ACR without storing credentials.

```
RESOURCE_GROUP="sre-databricks-rg"
REGION="eastus2"

az identity create \
  --name databricks-mcp-identity \
  --resource-group $RESOURCE_GROUP \
  --location $REGION
```

### 1.2 Grant ACR Pull Permission

```
ACR_NAME="myacr"  # Your ACR name
ACR_RG="acr-resource-group"  # Resource group where ACR lives

# Get identity principal ID
PRINCIPAL_ID=$(az identity show \
  --name databricks-mcp-identity \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Get ACR resource ID
ACR_ID=$(az acr show --name $ACR_NAME --resource-group $ACR_RG --query id -o tsv)

# Assign AcrPull role
az role assignment create \
  --assignee-object-id $PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope $ACR_ID
```

Expected output:

```
{
  "principalId": "...",
  "roleDefinitionName": "AcrPull",
  "scope": "/subscriptions/.../resourceGroups/sre-databricks-rg/providers/Microsoft.ContainerRegistry/registries/myacr"
}
```

### 1.3 Get Identity Resource ID

You'll need this for Step 5. Save it:

```
IDENTITY_ID=$(az identity show \
  --name databricks-mcp-identity \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

echo "Identity ID: $IDENTITY_ID"
# Save this output for Step 6.3
```

---

## Step 2: Prepare Local Source

```
cd zDatabricksMCP

# Verify structure (should have src/ folder with entry_http.py, pyproject.toml)
ls -la src/

# Expected output:
# - Dockerfile
# - entry_http.py
# - pyproject.toml
# - databricks_mcp/ (package folder)
```

---

## Step 3: Build Docker Image Locally

### 3.1 Create .env file (for local testing)

```
# Create src/.env
cat > src/.env << 'EOF'
DATABRICKS_HOST=https://adb-7405612783315468.8.azuredatabricks.net
DATABRICKS_TOKEN=your_token_here
DATABRICKS_WAREHOUSE_ID=your_warehouse_id_here
EOF
```

### 3.2 Build the image

```
cd src

# Build (5-10 minutes on first build, faster on subsequent builds with cache)
docker build -t databricks-mcp:latest .

# Verify build
docker images | grep databricks-mcp
```

Expected output:

```
databricks-mcp    latest    0ef5c9618bb9    246MB             0B
```

**Note**: If you see a warning about `SecretsUsedInArgOrEnv: ENV DATABRICKS_TOKEN`, this is expected behavior and can be safely ignored. The environment variables are placeholders and will be overridden by Azure Container Apps secrets.

---

## Step 4: Test Locally with Docker

### 4.1 Run container

```
docker run --rm \
  --env-file .env \
  -p 8000:8000 \
  --name databricks-mcp-test \
  databricks-mcp:latest
```

Expected output:

```
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 4.2 Test in another terminal (keep container running)

Open a **new terminal** while the container is still running:

```
# Test MCP endpoint from another terminal
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

Expected response:

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",...}}
```

✅ **If you see status 200 and JSON response**: MCP server is working correctly.

**✅ STEP 4 VALIDATED**: Local container test successful. Image builds, starts, and responds to MCP protocol.

### 4.3 Stop container

Return to the first terminal and press **Ctrl+C**, or from another terminal:

---

## Step 5: Push to Azure Container Registry

### 5.1 Login to ACR

```
ACR_NAME="myacr"  # Replace with your ACR name
ACR_URL="${ACR_NAME}.azurecr.io"

az acr login --name $ACR_NAME
```

### 5.2 Tag image

```
docker tag databricks-mcp:latest ${ACR_URL}/databricks-mcp:latest
docker tag databricks-mcp:latest ${ACR_URL}/databricks-mcp:final

# Verify tags
docker images | grep databricks-mcp
```

### 5.3 Push to ACR

```
docker push ${ACR_URL}/databricks-mcp:latest
docker push ${ACR_URL}/databricks-mcp:final

# Verify in ACR
az acr repository list --name $ACR_NAME
```

Expected output:

```
databricks-mcp
```

---

## Step 6: Deploy to Azure Container Apps

### 6.1 Set variables

```
RESOURCE_GROUP="sre-databricks-rg"
CONTAINER_APP_ENV="databricks-mcp-env"
CONTAINER_APP_NAME="databricks-mcp"
ACR_NAME="myacr"
ACR_URL="${ACR_NAME}.azurecr.io"
REGION="eastus2"
```

### 6.2 Create Container Apps Environment (if not exists)

```
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $REGION
```

### 6.3 Deploy or update Container App

**Important**: Replace `<sub-id>` with your subscription ID. You can get it from Step 1.3 `$IDENTITY_ID` or:

```
SUB_ID=$(az account show --query id -o tsv)
echo $SUB_ID
```

Then:

```
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image ${ACR_URL}/databricks-mcp:final \
  --ingress external \
  --target-port 8000 \
  --user-assigned /subscriptions/<sub-id>/resourceGroups/sre-databricks-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/databricks-mcp-identity \
  --registry-server $ACR_URL \
  --registry-identity /subscriptions/<sub-id>/resourceGroups/sre-databricks-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/databricks-mcp-identity \
  --env-vars DATABRICKS_HOST=$DATABRICKS_HOST DATABRICKS_WAREHOUSE_ID=$DATABRICKS_WAREHOUSE_ID
```

Or **update** existing Container App:

```
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_URL}/databricks-mcp:final \
  --registry-server $ACR_URL \
  --registry-identity /subscriptions/<sub-id>/resourceGroups/sre-databricks-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/databricks-mcp-identity \
  --set-env-vars DATABRICKS_HOST=$DATABRICKS_HOST DATABRICKS_WAREHOUSE_ID=$DATABRICKS_WAREHOUSE_ID
```

### 6.4 Store Databricks token as a secret

```
az containerapp secret set \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets databricks-token="$DATABRICKS_TOKEN"
```

Bind the secret to the environment:

```
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars DATABRICKS_TOKEN=secretref:databricks-token
```

Verify the token is wired:

```
python mcp_validate.py --base-url https://<container-app-url> --mode validate --warehouse-id <warehouse-id>
```

### 6.5 Get public URL

```
az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" -o tsv
```

Expected output:

```
databricks-mcp.<random>.eastus2.azurecontainerapps.io
```

---

## Step 7: Test Remote Endpoint

### 7.1 Test connectivity

```
ENDPOINT="https://<container-app-url>/mcp"

curl -X POST $ENDPOINT \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

Expected: Same JSON response as Step 3.2.

### 7.2 Test with Python client

Use the consolidated script:

```
pip install requests --quiet
python mcp_validate.py --base-url https://<container-app-url> --mode init
```

Optional modes:

```
# List tools (Step 8)
python mcp_validate.py --base-url https://<container-app-url> --mode list-tools

# Full validation suite (tools + sample calls)
python mcp_validate.py --base-url https://<container-app-url> --mode validate --warehouse-id <warehouse-id>

# Tool discovery only
python mcp_validate.py --base-url https://<container-app-url> --mode discover

# Natural language-style flow (runs tool calls with prompts)
python mcp_validate.py --base-url https://<container-app-url> --mode conversation --warehouse-id <warehouse-id>
```

Expected output:

```

Status: 200  
Response: event: message  
data: {"jsonrpc":"2.0",...}  
✅ MCP endpoint is working!
```

---

## Step 8: Test MCP Tools

### 8.1 List available tools

Use the consolidated script:

```
python mcp_validate.py --base-url https://<container-app-url> --mode list-tools
```

Expected output:

```
Tools available: 38
- list_clusters: List all Databricks clusters
- list_jobs: List Databricks jobs
- execute_sql: Execute a SQL statement
- list_catalogs: List Unity Catalog catalogs
- list_schemas: List schemas in a catalog
```

---

## Step 9: Verification Checklist

Before proceeding to SRE Agent integration:

*   Docker image builds without errors
*   Local container runs and responds to MCP requests
*   Image pushed to ACR successfully
*   Container App deployed and public endpoint accessible
*   Remote endpoint responds to initialize request (200 OK)
*   MCP tools list shows ≥35 tools (38 expected)
*   Validation run completes (warehouse listing may be skipped if tool not advertised)
*   No authentication errors in logs

Check logs:

```
az containerapp logs show \
  --name databricks-mcp \
  --resource-group sre-databricks-rg \
  --tail 50
```

---

## Step 10: Configure for SRE Agent Integration

Once verified, the MCP endpoint is ready for the Azure SRE Agent.

**Endpoint URL**: Get from Step 6.4

```
az containerapp show \
  --name databricks-mcp \
  --resource-group sre-databricks-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv
```

### 10.1 Add Azure SRE Agent Connector

Create a connector with:

```
Name: databricks-mcp
Connection type: streamable-http
URL: https://<container-app-url>/mcp
Auth method: Custom headers
Key: Accept
Value: application/json, text/event-stream
```

---

## Step 11: Create Subagent in Azure SRE Agent UI

Go to **Builder** > **Subagent builder** > **Create**.

Choose **YAML** and paste the contents of `Databricks_MCP_Agent.yaml`.

Save the subagent.

Add the MCP connector you created in Step 10.

Expected result: the connector shows the list of Databricks tools (as in the tools list view).

---

## Troubleshooting

### Container won't start

```
az containerapp logs show --name databricks-mcp --resource-group sre-databricks-rg
```

Look for: `DATABRICKS_TOKEN` or `DATABRICKS_HOST` not set.

### 400 Bad Request from MCP endpoint

Missing Accept header:

```
Accept: application/json, text/event-stream
```

### 404 Not Found

Verify URL includes `/mcp` path:

```
https://<container-app-url>/mcp
```

### No tools available

Check Databricks credentials in Container App secrets:

```
az containerapp show --name databricks-mcp --resource-group sre-databricks-rg \
  --query "properties.template.containers[0].env"
```

Confirm the secret exists:

```
az containerapp secret list --name databricks-mcp --resource-group sre-databricks-rg \
  --query "[].name" -o tsv
```

---

## Reference

*   [AZURE\_DATABRICKS\_BEST\_PRACTICES.md](AZURE_DATABRICKS_BEST_PRACTICES.md) - Validation criteria
*   [Databricks_MCP_Agent.yaml](Databricks_MCP_Agent.yaml) - SRE Agent configuration

---

**Last Updated**: February 11, 2026