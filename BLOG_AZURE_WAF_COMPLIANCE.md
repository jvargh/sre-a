# Azure WAF Compliance with MCP-Driven SRE Agent

Continuous Azure Well-Architected Framework compliance validation using AI - autonomous resource discovery, org practice enforcement, and one-click remediation via Model Context Protocol.

## Overview

Azure governance at scale is complex. Security teams manually review many resource types across multiple subscriptions. Finance can't track costs without tags. Compliance teams spend days cross-referencing WAF standards against actual infrastructure. And critical security gaps—like RDP open to 0.0.0.0/0 or customer-managed encryption disabled—slip through until discovered in audits.

This workflow is broken. Enter the **Azure SRE Agent**: an AI-powered compliance engine that discovers all resources, assesses them against all 5 WAF pillars AND your organization's specific standards in minutes, then generates exact remediation commands with quantified impact.

**How it works:**

The agent leverages these capabilities to transform Azure governance:

**Autonomous Resource Discovery via MCP** - Azure MCP (Model Context Protocol) server exposes Azure Resource Graph and ARM APIs as discoverable tools. The agent automatically inventories all resources across subscriptions with metadata (types, locations, tags, security settings) in seconds.

**Multi-Pillar WAF Assessment** - For each discovered resource, the agent validates against all 5 WAF pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance) using Azure MCP tools, generating an assessment summary with pass/fail/partial/unknown counts.

**Org Best Practices Cross-Check** - The agent references your organization's compliance standards (stored in knowledge base as `org-practices.md`) to escalate WAF findings into actionable org policies. A Security policy violation becomes a critical finding. A cost optimization recommendation becomes a warning.

**Automated Remediation Codegen** - For every finding, the agent generates exact Azure CLI commands, Terraform snippets, and Portal steps with impact quantification (risk reduction, cost savings, compliance improvement).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure SRE Agent                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ WAF Agent    │  │ Azure MCP    │  │ Org Best     │       │
│  │ Config       │  │ Connector    │  │ Practices KB │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ MCP Protocol (HTTPS)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Azure MCP Server (Azure Container Apps)             │
│         - Resource Graph queries                            │
│         - ARM API tools (VMs, Storage, NSGs, etc.)          │
│         - Cost Management, Monitor, Key Vault APIs          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Azure REST APIs
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure Subscription Resources                   │
│   VMs • Storage • NSGs • Key Vaults • App Services • etc.   │
└─────────────────────────────────────────────────────────────┘
```

The Azure SRE Agent orchestrates WAF compliance checks by calling Azure MCP tools to discover and assess resources, then cross-references findings with organizational best practices from the knowledge base. End-to-end: subscription scope → resource discovery → 5-pillar assessment → org compliance → remediation commands.

---

## Deployment

The Azure MCP server runs locally via Node.js in **Stdio mode**, communicating with the SRE Agent through standard input/output. Configured with Managed Identity credentials, it exposes Azure ARM and governance APIs as MPC tools. The agent uses this catalog plus the org practices knowledge base to validate compliance autonomously.

**Scheduling Options:**

*   **Ad-hoc**: Run on-demand via agent prompt
*   **Scheduled**: Azure Logic Apps or Azure Functions trigger (daily/weekly compliance scans)
*   **Event-driven**: Trigger on resource group changes or policy violations

---

## Getting Started

**Configure Azure MCP Connector**:

**Connection Type**: Stdio (local process)

**Command**: `npx`

**Arguments** (in order):

*   `-y` (auto-accept)
*   `@azure/mcp` (package name)
*   `server` (run as server)
*   `start` (start command)
*   `--mode` (mode flag)
*   `all` (enable all resources)

**Environment Variables**:

*   `AZURE_CLIENT_ID`: Your managed identity client ID
*   `AZURE_TOKEN_CREDENTIALS`: `managedidentitycredential`

**Managed Identity**: Select your managed identity from dropdown

**Configure Azure SRE Agent**:

*   Upload Knowledge Base from Builder > Knowledge Base using the org practices doc: [org-practices.md](https://github.com/jvargh/sre-a/blob/main/databricks-srea/org-practices.md)
*   Benefit: Agent validates Azure resources against both WAF standards AND your company-specific requirements
*   Deploy the agent YAML: [Azure\_WAF\_Compliance\_Agent.yaml](https://github.com/jvargh/sre-a/blob/main/databricks-srea/Azure_WAF_Compliance_Agent.yaml)
*   Benefit: Autonomous resource discovery + 5-pillar assessment + org compliance in one execution

**Run Your First Validation**:

Prompt the agent with your subscription or resource group:

```
@Azure_WAF_Compliance_Agent: Assess resource group "sre-demo2-rg" found in subscription id 
"<your-subscription-id>" against all 5 WAF pillars and org-practices.md compliance. 
Identify gaps, flag critical findings, and provide remediation steps.
```

**Integrate with Operations**:

*   Schedule daily compliance scans via Azure Logic Apps
*   Trigger assessments on resource deployments
*   Export findings to Azure DevOps or ServiceNow for ticketing

---

## Autonomous Compliance Workflow

### Phase 1: Resource Discovery

**Agent Task:**

The agent automatically discovers all resources in the target resource group, including VMs, storage accounts, NSGs, Key Vaults, App Services, and more - no manual resource IDs needed.

**What the Agent Does:**

Calls Azure MCP tools in parallel:

*   `list_virtual_machines()` - Inventory compute
*   `list_storage_accounts()` - Inventory storage
*   `list_network_security_groups()` - Inventory network security
*   `list_key_vaults()` - Inventory secrets management
*   `list_web_apps()` - Inventory App Services
*   Additional resource type queries as needed

Builds comprehensive resource inventory with metadata (types, locations, tags, configurations)

**Expected Output:**

```
📋 Resource Discovery Complete

Resource Group: <sre-resource-group>
Subscription: <subscription-id>

Discovered Resources:
- Compute VMs: 2 (Linux Ubuntu, Windows Server)
- AKS Cluster: 1 (prod-aks-cluster-01)
- Function App: 1 (data-processor-func)
- SQL Server: 1 (prod-sql-server-01)
- Storage Accounts: 4 (diagnostics, logs, data, backups)
- Network Security Groups: 3
- Key Vaults: 2
- Virtual Networks: 2
- Public IPs: 3
- Application Gateways: 1
- Policy Assignments: 8 active

Next: Assessing all resources against 5 WAF pillars and 8 security policies...
```

---

### Phase 2: Multi-Pillar WAF Assessment

**Agent Task:**

For each discovered resource, the agent validates against all 5 Azure Well-Architected Framework pillars using Azure MCP tools.

**What the Agent Does:**

**Reliability Pillar:**

*   VM availability zones, backup configuration, health probes
*   Storage redundancy (LRS vs GRS vs ZRS)
*   App Service health checks and auto-healing

**Security Pillar:**

*   NSG rules: Check for 0.0.0.0/0 sources on SSH/RDP
*   Key Vault: Secret expiration dates, soft delete, purge protection
*   Storage: Public blob access, shared key access, HTTPS enforcement, TLS version
*   App Service: HTTPS-only, managed identity, VNet integration

**Cost Optimization Pillar:**

*   VM right-sizing: CPU/memory utilization analysis
*   Orphaned resources: Unattached disks, unused public IPs
*   Resource tagging: cost-center, owner, environment tags
*   Storage tiering opportunities

**Operational Excellence Pillar:**

*   Monitoring: Azure Monitor diagnostics enabled
*   Logging: Log Analytics workspace integration
*   IaC: Resource tags indicating Terraform/Bicep management

**Performance Pillar:**

*   VM series appropriateness for workload
*   Storage account performance tier
*   App Service plan scaling configuration

**Expected Output:**

```
✅ WAF Assessment Complete

📊 Pillar Summary:
┌────────────────────────┬──────┬──────┬─────────┬─────────┐
│ Pillar                 │ Pass │ Fail │ Partial │ Unknown │
├────────────────────────┼──────┼──────┼─────────┼─────────┤
│ Reliability            │  14  │  3   │   2     │   0     │
│ Security               │  10  │  8   │   1     │   2     │
│ Cost Optimization      │   8  │  5   │   3     │   0     │
│ Operational Excellence │  12  │  4   │   2     │   1     │
│ Performance            │  11  │  3   │   1     │   2     │
└────────────────────────┴──────┴──────┴─────────┴─────────┘

📋 Policy Compliance:
- Policies Passed: 5/8 (63%)
- Policies Flagged: 3/8 (37%)

🔴 Critical Findings: 8
🟡 Warnings: 11
🔵 Info: 15
```

---

### Phase 3: Org Best Practices Cross-Check

**Agent Task:**

Cross-reference all WAF findings with organizational requirements from `org-practices.md` knowledge base. Escalate violations of company-specific standards.

**What the Agent Does:**

Reads org-practices.md from knowledge base

For each WAF finding, checks if it intersects with org requirement

Maps severity based on org standards:

*   🔴 **Critical**: NSG open to 0.0.0.0/0, Key Vault secrets expiring \< 30 days, storage public access enabled
*   🟡 **Warning**: Missing required tags (cost-center, owner), idle VMs, orphaned disks
*   🔵 **Info**: Recommendations without org mandate

Provides specific evidence and references to org-practices.md sections

**Expected Output:**

```
🔍 Org Compliance Cross-Check

🔴 CRITICAL (8 findings):

1. Security Policy Violation: SQL Database "prod-sql-db" TLS version < 1.2
   - WAF Pillar: Security
   - Policy: "SQL databases must require TLS 1.2 minimum"
   - Resource: prod-sql-server-01/prod-sql-db
   - Evidence: minTlsVersion = 1.0 (unsupported)
   - Impact: HIGH - Vulnerable to downgrade attacks
   - Reference: org-practices.md § SQL Configuration

2. Security Policy Violation: AKS Cluster "prod-aks-cluster-01" RBAC disabled
   - WAF Pillar: Security
   - Policy: "All AKS clusters must have RBAC enabled"
   - Resource: prod-aks-cluster-01
   - Evidence: rbacEnabled = false
   - Impact: HIGH - Uncontrolled cluster access
   - Reference: org-practices.md § Kubernetes Security

3. Security Policy Violation: Storage Account "diagstorage01" encryption at rest disabled
   - WAF Pillar: Security
   - Policy: "Customer-managed encryption keys required for all storage"
   - Resource: diagstorage01 (Microsoft-managed keys only)
   - Evidence: encryptionSource = "Microsoft.Storage"
   - Impact: HIGH - Data at rest not encrypted with org keys
   - Reference: org-practices.md § Storage Encryption

4. Compute VM "ubuntu-prod-01" missing security extension
   - WAF Pillar: Security
   - Policy: "All VMs must have Azure Monitor VM extension installed"
   - Resource: ubuntu-prod-01
   - Evidence: Extensions = ["DSC"] (no monitoring)
   - Impact: MEDIUM - No endpoint protection or logging
   - Reference: org-practices.md § VM Security

5. Function App "data-processor-func" HTTPS-only disabled
   - WAF Pillar: Security
   - Policy: "All app services must enforce HTTPS"
   - Resource: data-processor-func
   - Evidence: httpsOnly = false
   - Impact: MEDIUM - Data in transit transmitted over HTTP
   - Reference: org-practices.md § App Service Configuration

6. Key Vault "kv-prod-01" purge protection disabled
   - WAF Pillar: Security
   - Policy: "Key Vaults must have purge protection enabled"
   - Resource: kv-prod-01
   - Evidence: purgeProtectionEnabled = false
   - Impact: MEDIUM - Secrets can be permanently deleted without recovery
   - Reference: org-practices.md § Key Vault Security

7. NSG "nsg-aks-nodes" allows port 3389 (RDP) from 0.0.0.0/0
   - WAF Pillar: Security
   - Policy: "No inbound RDP access from internet"
   - Resource: NSG rule "AllowRDP" on port 3389
   - Evidence: Source = "*", Protocol = "TCP"
   - Impact: CRITICAL - Exposed to brute-force attacks
   - Reference: org-practices.md § Network Security

8. SQL "prod-sql-server-01" auditing not configured
   - WAF Pillar: Operational Excellence
   - Policy: "SQL Server auditing must be enabled"
   - Resource: prod-sql-server-01
   - Evidence: auditingPolicy.state = "Disabled"
   - Impact: MEDIUM - No compliance trail for database access
   - Reference: org-practices.md § SQL Audit Requirements

🟡 WARNING (11 findings):

9. Compute VM "win-dev-02" unassigned managed identity
   - WAF Pillar: Security
   - Policy: "All VMs should use managed identity"
   - Evidence: No system-assigned or user-assigned identity
   - Reference: org-practices.md § Managed Identity

10. VM "ubuntu-prod-01" missing required tag "cost-center"
    - WAF Pillar: Cost Optimization
    - Policy: "Mandatory Tags for ALL Resources"
    - Resource: Tags = { "environment": "prod" }
    - Evidence: Missing cost-center, owner, project tags
    - Reference: org-practices.md § Tagging Requirements

11. Managed Disk "disk-unattached-03" orphaned for 9 days
    - WAF Pillar: Cost Optimization
    - Policy: "Disks not attached for 7+ days must be reviewed"
    - Resource: disk-unattached-03 (256 GB Premium SSD)
    - Evidence: Last detached: 2026-02-03
    - Cost Impact: $48/month wasted
    - Reference: org-practices.md § Orphaned Resources

12. Storage Account "logsstorage01" lifecycle policy not configured
    - WAF Pillar: Cost Optimization
    - Policy: "Storage with logs/diagnostics must have tiering"
    - Evidence: No tiering or deletion policy set
    - Cost Impact: $120/month on hot tier retention
    - Reference: org-practices.md § Storage Tiering

13. Function App Consumption Plan "data-processor-func" missing monitoring
    - WAF Pillar: Operational Excellence
    - Policy: "All Function Apps must have Application Insights"
    - Evidence: No monitoring configured
    - Reference: org-practices.md § Application Monitoring

14. Virtual Network "vnet-prod" missing NSG on subnets
    - WAF Pillar: Security
    - Policy: "All subnets must have NSG associations"
    - Resource: prod-subnet-01 (unprotected)
    - Evidence: 2 of 5 subnets missing NSGs
    - Reference: org-practices.md § Network Segmentation

15. AKS "prod-aks-cluster-01" network policy disabled
    - WAF Pillar: Security
    - Policy: "AKS must have Calico network policies enabled"
    - Evidence: networkPolicy.provider = "none"
    - Reference: org-practices.md § Kubernetes Networking
```

---

### Phase 4: Remediation with Exact Commands

**Agent Task:**

Generate copy-paste CLI commands, Terraform snippets, and Portal steps for every gap. Quantify impact (cost savings, risk reduction).

**What the Agent Does:**

1.  For each finding, generates precise fix commands
2.  Provides Azure CLI, PowerShell, or Terraform as appropriate
3.  Quantifies impact: cost reduction, security risk level, compliance improvement

**Expected Output:**

```
🛠️ Remediation Steps

🔴 CRITICAL Remediations (Immediate Action - Deploy Today):

─────────────────────────────────────────────────────────────
1. Fix SQL Server TLS 1.2 minimum requirement

📋 Copy-Paste Command:
az sql server update \
  --resource-group sre-westus2-rg \
  --name prod-sql-server-01 \
  --minimal-tls-version 1.2

Impact:
  - Risk Reduction: CRITICAL (prevents TLS downgrade attacks)
  - Compliance: Closes policy violation
  - Time to remediate: 2 minutes

─────────────────────────────────────────────────────────────
2. Enable RBAC on AKS Cluster "prod-aks-cluster-01"

📋 Note: RBAC requires cluster recreation
az aks create \
  --resource-group sre-westus2-rg \
  --name prod-aks-cluster-01 \
  --enable-rbac \
  --enable-managed-identity

# Or use Azure Portal > Cluster properties > Enable RBAC + recreate

Impact:
  - Risk Reduction: CRITICAL (enables access control)
  - Compliance: Resolves AKS security policy
  - Downtime: ~15-20 minutes cluster recreation

─────────────────────────────────────────────────────────────
3. Enable Customer-Managed Encryption on Storage "diagstorage01"

📋 Copy-Paste Commands:
# Create key vault (if not exists)
az keyvault create \
  --resource-group sre-westus2-rg \
  --name kv-storage-keys-01 \
  --location westus2

# Create encryption key
az keyvault key create \
  --vault-name kv-storage-keys-01 \
  --name storage-cmk-01 \
  --protection software

# Enable customer-managed encryption
az storage account update \
  --resource-group sre-westus2-rg \
  --name diagstorage01 \
  --encryption-key-source Microsoft.Keyvault \
  --encryption-key-vault https://kv-storage-keys-01.vault.azure.net/ \
  --encryption-key-name storage-cmk-01

Impact:
  - Risk Reduction: HIGH (data at rest encrypted with org keys)
  - Compliance: Closes CMK encryption policy violation
  - Cost Impact: +$30/month for key vault operations

─────────────────────────────────────────────────────────────
4. Fix NSG "nsg-aks-nodes" - Remove RDP from 0.0.0.0/0

📋 Copy-Paste Command:
az network nsg rule update \
  --resource-group sre-westus2-rg \
  --nsg-name nsg-aks-nodes \
  --name AllowRDP \
  --source-address-prefixes 10.0.0.0/8 192.168.0.0/16

Or delete and use Azure Bastion:
az network nsg rule delete \
  --resource-group sre-westus2-rg \
  --nsg-name nsg-aks-nodes \
  --name AllowRDP

az network bastion create \
  --resource-group sre-westus2-rg \
  --name bastion-prod \
  --vnet-name vnet-prod \
  --location westus2 \
  --public-ip-address bastion-pip

Impact:
  - Risk Reduction: CRITICAL (prevents RDP brute-force attacks)
  - Compliance: Closes network security policy
  - Time to remediate: 5 minutes (NSG rule), 20 minutes (Bastion)

─────────────────────────────────────────────────────────────
5. Enable SQL Server Auditing

📋 Copy-Paste Commands:
az sql server audit-policy update \
  --resource-group sre-westus2-rg \
  --name prod-sql-server-01 \
  --state Enabled \
  --storage-endpoint https://logstorage01.blob.core.windows.net \
  --storage-key <storage-account-key> \
  --retention-days 90

# Or enable to Log Analytics
az sql server audit-policy update \
  --resource-group sre-westus2-rg \
  --name prod-sql-server-01 \
  --state Enabled \
  --log-analytics-target-state Enabled \
  --log-analytics-workspace /subscriptions/<sub-id>/resourcegroups/sre-westus2-rg/providers/microsoft.operationalinsights/workspaces/law-prod

Impact:
  - Risk Reduction: MEDIUM (audit trail enables compliance investigation)
  - Compliance: Resolves SQL audit requirement
  - Cost Impact: +$8/month (Log Analytics)

─────────────────────────────────────────────────────────────
6. Enable Azure Monitor VM Extension on "ubuntu-prod-01"

📋 Copy-Paste Commands:
# Install Log Analytics agent extension
az vm extension set \
  --resource-group sre-westus2-rg \
  --vm-name ubuntu-prod-01 \
  --name DependencyAgentLinux \
  --publisher Microsoft.Azure.Monitoring.DependencyAgent \
  --version 9.10 \
  --auto-upgrade-minor-version true

# Install monitoring agent
az vm extension set \
  --resource-group sre-westus2-rg \
  --vm-name ubuntu-prod-01 \
  --name AzureMonitoringLinuxAgent \
  --publisher Microsoft.Azure.Monitor \
  --version 1.23 \
  --auto-upgrade-minor-version true

Impact:
  - Risk Reduction: MEDIUM (enables endpoint monitoring + logging)
  - Compliance: Resolves VM security monitoring requirement
  - Cost Impact: +$15/month per VM (Log Analytics)

─────────────────────────────────────────────────────────────

🟡 WARNING Remediations (Schedule within 7 days):

─────────────────────────────────────────────────────────────
7. Enable HTTPS-only on Function App "data-processor-func"

📋 Copy-Paste Command:
az functionapp update \
  --resource-group sre-westus2-rg \
  --name data-processor-func \
  --set httpsOnly=true

Impact:
  - Risk Reduction: MEDIUM (data in transit encrypted)
  - Compliance: Resolves HTTPS enforcement policy
  - Time to remediate: 1 minute

─────────────────────────────────────────────────────────────
8. Enable Purge Protection on Key Vault "kv-prod-01"

📋 Copy-Paste Command:
az keyvault update \
  --resource-group sre-westus2-rg \
  --name kv-prod-01 \
  --enable-purge-protection true

Impact:
  - Risk Reduction: MEDIUM (prevents accidental secret deletion)
  - Compliance: Resolves Key Vault security policy
  - Time to remediate: 1 minute

─────────────────────────────────────────────────────────────
9. Delete Orphaned Disk "disk-unattached-03"

📋 Copy-Paste Commands:
# Create snapshot first (recommended)
az snapshot create \
  --resource-group sre-westus2-rg \
  --name snapshot-disk-unattached-03 \
  --source-resource-group sre-westus2-rg \
  --source-resource-id /subscriptions/<sub-id>/resourceGroups/sre-westus2-rg/providers/Microsoft.Compute/disks/disk-unattached-03

# Delete disk
az disk delete \
  --resource-group sre-westus2-rg \
  --name disk-unattached-03 \
  --yes

Impact:
  - Cost Savings: $48/month (256 GB Premium SSD)
  - Compliance: Resolves orphaned resource policy
  - Time to remediate: 3 minutes

─────────────────────────────────────────────────────────────
10. Configure Storage Lifecycle Policy on "logsstorage01"

📋 Copy-Paste Command:
az storage account management-policy create \
  --resource-group sre-westus2-rg \
  --account-name logsstorage01 \
  --policy @- <<'EOF'
{
  "rules": [
    {
      "name": "archive-old-logs",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {"blobTypes": ["blockBlob"]},
        "actions": {
          "baseBlob": {
            "tierToCool": {"daysAfterModificationGreaterThan": 30},
            "tierToArchive": {"daysAfterModificationGreaterThan": 90},
            "delete": {"daysAfterModificationGreaterThan": 365}
          }
        }
      }
    }
  ]
}
EOF

Impact:
  - Cost Savings: $120/month (hot->cool->archive tiering)
  - Compliance: Resolves storage tiering policy
  - Time to remediate: 5 minutes

─────────────────────────────────────────────────────────────
11. Add Monitoring to Function App "data-processor-func"

📋 Copy-Paste Command:
az functionapp config appsettings set \
  --resource-group sre-westus2-rg \
  --name data-processor-func \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=<key> \
             ApplicationInsightsAgent_EXTENSION_VERSION=~3

Impact:
  - Risk Reduction: MEDIUM (enables performance + error tracking)
  - Compliance: Resolves monitoring requirement
  - Cost Impact: +$12/month (Application Insights)

─────────────────────────────────────────────────────────────
12. Add Tags to VM "ubuntu-prod-01"

📋 Copy-Paste Command:
az vm update \
  --resource-group sre-westus2-rg \
  --name ubuntu-prod-01 \
  --set tags.cost-center=engineering \
           tags.owner=platform-team \
           tags.environment=prod \
           tags.project=data-pipeline

Impact:
  - Cost Tracking: Enables finance cost allocation
  - Compliance: Resolves tagging policy
  - Time to remediate: 1 minute

─────────────────────────────────────────────────────────────
```

---

### Remediation Roadmap

**Immediate (Deploy Today - Critical Risk):**

1.  Enable TLS 1.2 minimum on SQL Server prod-sql-server-01 (2 min)
2.  Fix NSG "nsg-aks-nodes" - Remove RDP from 0.0.0.0/0 (5 min)
3.  Enable SQL Server Auditing (10 min)
4.  Enable RBAC on AKS Cluster (recreate cluster, ~20 min downtime)
5.  Enable Customer-Managed Encryption on diagstorage01 (15 min)

**Short-Term (Next 3 Days - High Risk):**

1.  Install Azure Monitor VM extensions on ubuntu-prod-01 (10 min)
2.  Enable HTTPS-only on Function App data-processor-func (1 min)
3.  Enable Purge Protection on Key Vault kv-prod-01 (1 min)
4.  Deploy Azure Bastion for secure VM access (20 min)
5.  Enable AKS Calico network policies (10 min)

**Short-Term (1 Week - Medium Risk):**

1.  Delete orphaned disk disk-unattached-03 ($48/month savings)
2.  Configure storage lifecycle policy on logsstorage01 ($120/month savings)
3.  Add monitoring to Function App data-processor-func
4.  Add required tags to VM ubuntu-prod-01 and others
5.  Add NSG to unprotected subnets in vnet-prod

**Medium-Term (2-4 Weeks - Low Risk):**

1.  Implement automated secret rotation for Key Vault
2.  Configure Application Insights for all Function Apps
3.  Set up managed identity on win-dev-02 and other VMs
4.  Implement Azure Policy enforcement for ongoing compliance

**Long-Term (Ongoing - Preventive):**

1.  Schedule weekly compliance scans via Azure Logic Apps
2.  Integrate findings with Azure DevOps for backlog tracking
3.  Implement GitOps for IaC enforcement (Terraform, Bicep)
4.  Train teams on security best practices and compliance requirements

---

## Real-World Results

The assessment workflow discovered **8 critical findings and 11 warnings** across SQL, AKS, Storage, VMs, and NSGs. Each came with remediation commands and prioritized timelines. **Total time: 6 minutes**. Manual review would take 4-6 hours.

---

## Key Benefits

### Autonomous Discovery & Assessment

*   ✅ Zero manual resource inventory—agent discovers everything
*   ✅ Multi-pillar WAF validation in one execution
*   ✅ Org-specific compliance enforcement via knowledge base

### Risk & Cost Visibility

*   🔴 Immediate identification of critical security gaps (NSGs, secrets, public storage)
*   💰 Quantified cost savings from orphaned resources and idle VMs
*   📊 Evidence-based findings with direct references to org policies

### Actionable Remediation

*   🛠️ Copy-paste CLI commands and Terraform for every gap
*   ⚡ Prioritized roadmap (immediate/short/medium/long-term)
*   📈 Impact quantification (risk reduction, cost savings, compliance %)

### Operational Impact

| Metric | Before | After | Improvement |
| --- | --- | --- | --- |
| WAF compliance review | 4-6 hours manual | 5-8 minutes autonomous | **95%** |
| Critical security gap discovery | 2-3 days | Real-time | **Immediate** |
| Org policy violation tracking | Manual spreadsheet | Automated report | **100%** |
| Orphaned resource cleanup | Quarterly review | Weekly automated scan | **4x frequency** |

---

## Scheduling Compliance Scans

### Option 1: Ad-Hoc Execution

Run compliance checks on-demand via agent prompt when needed.

### Option 2: Scheduled (Recommended)

Azure SRE Agent has built-in scheduled task management. Create a new scheduled task with:

**Configuration:**
- **Frequency**: Daily, Weekly, Monthly
- **Time of Day**: Set scan execution time (e.g., 5:15 PM)
- **Start Date**: When to begin scheduled scans
- **Task Details**: Specify the compliance assessment scope (resource group, subscription)
- **Response Subagent**: Select the Azure SRE Agent for compliance scanning
- **Autonomy Level**: Choose between Autonomous (auto-remediate) or Review (approval required)

**Example Setup:**
- Daily compliance scan at 8:00 AM
- Scope: Resource group "sre-westus2-rg"
- Autonomy: Review mode (agent requests approval before remediation)
- Run limit: No limit (continuous scanning enabled)

The agent automatically discovers resources, assesses WAF compliance, and either executes or flags remediation based on your autonomy settings.

---

## Conclusion

Azure SRE Agent transforms Azure governance by combining autonomous resource discovery, multi-pillar WAF assessment, and organization-specific compliance enforcement. The MCP integration provides:

*   **Continuous compliance** monitoring across all 5 WAF pillars
*   **Org best practices** enforcement via knowledge base integration
*   **Automated remediation** with exact CLI commands and impact quantification
*   **Flexible scheduling** for ad-hoc, scheduled, or event-driven scans

**Result**: Security teams maintain compliance effortlessly, finance tracks costs accurately, and platform teams remediate gaps with confidence.

---

## Resources

*   🤖 [Agent Configuration YAML](https://github.com/jvargh/sre-a/blob/main/databricks-srea/Azure_WAF_Compliance_Agent.yaml)
*   📋 [Org Best Practices](https://github.com/jvargh/sre-a/blob/main/databricks-srea/org-practices.md)
*   ⚙️ [Azure MCP Stdio Setup Guide](https://github.com/jvargh/sre-a/blob/main/zDocs/AZURE-MCP-STDIO-SETUP.md)
*   📖 [Azure SRE Agent Documentation](https://learn.microsoft.com/en-us/azure/sre-agent/)
*   📰 [Azure SRE Agent Blogs](https://techcommunity.microsoft.com/tag/azure%20sre%20agent?nodeId=board%3AAppsonAzureBlog)
*   📜 [MCP Specification](https://modelcontextprotocol.io/specification/)
*   🏗️ [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/)

---

**Questions?** Open an issue on GitHub or reach out to the Azure SRE team.