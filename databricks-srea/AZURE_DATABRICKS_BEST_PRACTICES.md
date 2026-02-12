# Azure Databricks Best Practices for Agents

**Purpose:** Agent-executable guidelines for Azure Databricks operations, optimized for Serverless compute and Unity Catalog environments.

**Target Audience:** Automated agents, SREs, operators managing Azure Databricks workloads

**Reference:** [Azure Well-Architected Framework - Databricks Guide](https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-databricks)

---

## Quick Context

This customer uses:

*   ✅ **Serverless Databricks** (SQL Warehouses, Serverless Compute)
*   ✅ **Unity Catalog** (Centralized governance)
*   ✅ **Delta Lake** (ACID transactions, time travel)
*   ✅ **Premium Tier** (Enhanced security, compliance)

---

## 1\. Reliability

### Agent Actions

**1.1 Configure Autoscaling**

```
# Check cluster autoscaling settings
az databricks cluster get --cluster-id <id> | jq '.autoscale'

# Verify: min_workers >= 2, max_workers within quota, target 70-80% utilization
```

**1.2 Enable Serverless SQL Warehouses**

*   ✅ Use serverless SQL for ad-hoc analytics (eliminates cluster management)
*   ✅ Configure auto-stop: 10-15 minutes idle timeout
*   ✅ Verify: Built-in high availability, automatic scaling

**1.3 Activate Delta Lake Reliability**

```
-- Enable time travel (7-30 days retention for production)
ALTER TABLE <table_name> SET TBLPROPERTIES (
  'delta.logRetentionDuration' = '7 days',
  'delta.deletedFileRetentionDuration' = '7 days'
);

-- Verify ACID transactions enabled (default for Delta)
DESCRIBE DETAIL <table_name>;
```

**1.4 Configure Job Retry Policies**

```
{
  "max_retries": 3,
  "timeout_seconds": 3600,
  "retry_on_timeout": true,
  "min_retry_interval_millis": 30000
}
```

**1.5 Implement Health Monitoring**

```
# Enable diagnostic logs
az monitor diagnostic-settings create \
  --resource <workspace-id> \
  --name databricks-logs \
  --workspace <log-analytics-id> \
  --logs '[{"category": "clusters", "enabled": true}, 
          {"category": "jobs", "enabled": true},
          {"category": "notebook", "enabled": true}]'
```

**1.6 Backup Workspace Metadata**

```
# Export workspace configurations (schedule daily)
databricks workspace export_dir / /backup --overwrite
databricks jobs list --output JSON > jobs-backup.json
databricks clusters list --output JSON > clusters-backup.json
```

---

## 2\. Security

### Agent Actions

**2.1 Deploy Unity Catalog**

```
# Verify Unity Catalog enabled
az databricks workspace show --name <workspace> | jq '.parameters.enableUnityMetastore'

# Required: Must be true for centralized governance
```

**2.2 Configure VNet Injection**

```
# Check VNet injection status
az databricks workspace show --name <workspace> | jq '.parameters.customVirtualNetworkId'

# Verify: Custom VNet ID present, not null
```

**2.3 Enable Private Link**

```
# Verify no public network access
az databricks workspace show --name <workspace> | jq '.parameters.publicNetworkAccess'

# Expected: "Disabled"
```

**2.4 Activate Customer-Managed Keys (CMK)**

```
# Check encryption configuration
az databricks workspace show --name <workspace> | jq '.parameters.encryption'

# Verify: CMK configured via Azure Key Vault
```

**2.5 Configure Secret Scopes (Azure Key Vault-backed)**

```python
# Create Key Vault-backed scope
databricks secrets create-scope --scope <scope-name> \
  --scope-backend-type AZURE_KEYVAULT \
  --resource-id <keyvault-id> \
  --dns-name <keyvault-url>

# DO NOT use Databricks-managed secrets for production
```

**2.6 Enable Audit Logging**

```
# Verify Unity Catalog audit logs
az monitor diagnostic-settings list --resource <workspace-id>

# Required categories: workspace, accounts, unityCatalog
```

**2.7 Configure Secure Cluster Connectivity**

```
# Verify no public IPs on clusters
az databricks cluster get --cluster-id <id> | jq '.enable_elastic_disk, .enable_local_disk_encryption, .ssh_public_keys'

# Expected: no public IPs, encryption enabled, no SSH keys
```

**2.8 Implement IP Access Lists**

```
# Configure allowed IPs (production only)
databricks ip-access-lists create \
  --list-type "ALLOW" \
  --ip-addresses "10.0.0.0/8,172.16.0.0/12"
```

---

## 3\. Cost Optimization

### Agent Actions

**3.1 Use Serverless for Variable Workloads**

*   ✅ Serverless SQL: 30-50% cheaper than always-on clusters
*   ✅ Serverless Jobs: Eliminates idle time costs
*   ✅ Auto-stop configured: 10-15 min idle timeout

**3.2 Configure Auto-Termination**

```
# Check all clusters have auto-termination
az databricks cluster list | jq '.clusters[] | {id, auto_termination_minutes}'

# Enforce: Dev clusters 30-60 min, interactive 15-30 min
```

**3.3 Implement Compute Policies**

```
{
  "policy_name": "cost-optimized",
  "definition": {
    "cluster_type": {
      "type": "fixed",
      "value": "job"
    },
    "autoscale": {
      "min_workers": {
        "type": "fixed",
        "value": 1
      },
      "max_workers": {
        "type": "range",
        "maxValue": 10
      }
    },
    "autotermination_minutes": {
      "type": "fixed",
      "value": 30
    }
  }
}
```

**3.4 Optimize Delta Lake Storage**

```
-- Run daily on high-volume tables
OPTIMIZE <table_name>;

-- Run weekly to remove old versions
VACUUM <table_name> RETAIN 168 HOURS; -- 7 days

-- Check storage costs
SELECT 
  table_name,
  size_bytes / 1024 / 1024 / 1024 as size_gb,
  num_files
FROM system.information_schema.table_storage_metrics
WHERE size_gb > 100
ORDER BY size_gb DESC;
```

**3.5 Monitor DBU Consumption**

```
-- Query system tables for cost tracking
SELECT 
  usage_date,
  workspace_id,
  sku_name,
  SUM(usage_quantity) as total_dbus
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY usage_date, workspace_id, sku_name
ORDER BY usage_date DESC;
```

**3.6 Tag Resources for Chargeback**

```
# Apply cost center tags
az databricks workspace update \
  --name <workspace> \
  --tags "CostCenter=Engineering" "Project=Analytics" "Environment=Production"
```

---

## 4\. Operational Excellence

### Agent Actions

**4.1 Implement Infrastructure as Code (IaC)**

```
# Use Databricks Asset Bundles
databricks bundle init

# Structure: Include notebooks, jobs, clusters, policies
# Version control: Git repository with CI/CD pipeline
```

**4.2 Configure Diagnostic Logging (All Categories)**

```
az monitor diagnostic-settings create \
  --resource <workspace-id> \
  --name databricks-full-logs \
  --workspace <log-analytics-id> \
  --logs '[
    {"category": "workspace", "enabled": true},
    {"category": "clusters", "enabled": true},
    {"category": "jobs", "enabled": true},
    {"category": "notebook", "enabled": true},
    {"category": "accounts", "enabled": true},
    {"category": "unityCatalog", "enabled": true}
  ]'
```

**4.3 Deploy Lakeflow Declarative Pipelines**

```python
# Use DLT for production pipelines (automatic quality enforcement)
import dlt

@dlt.table(
    name="validated_data",
    expectations={
        "valid_id": "id IS NOT NULL",
        "valid_timestamp": "timestamp >= '2020-01-01'"
    }
)
def create_validated_table():
    return spark.read.table("raw_data")
```

**4.4 Automate Workspace Backups**

```
# Schedule with Azure Automation or Azure Functions (daily)
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d)
databricks workspace export_dir / /backups/$BACKUP_DATE --overwrite
databricks jobs list --output JSON > /backups/$BACKUP_DATE/jobs.json
# Upload to Azure Storage with cross-region replication
az storage blob upload --account-name <storage> --container backups
```

**4.5 Set Up Cost Alerts**

```
# Create budget alert
az consumption budget create \
  --amount 10000 \
  --budget-name databricks-monthly \
  --time-period "2026-02-01" "2026-12-31" \
  --notifications "Actual_GreaterThan_80_Percent"
```

**4.6 Implement Cluster Lifecycle Policies**

```
{
  "policy_name": "governance-standard",
  "definition": {
    "spark_version": {
      "type": "fixed",
      "value": "13.3.x-scala2.12"
    },
    "node_type_id": {
      "type": "allowlist",
      "values": ["Standard_DS3_v2", "Standard_DS4_v2"]
    },
    "autotermination_minutes": {
      "type": "fixed",
      "value": 120
    }
  }
}
```

---

## 5\. Performance Efficiency

### Agent Actions

**5.1 Enable Photon Acceleration**

```
# Verify Photon enabled on clusters/warehouses
az databricks cluster get --cluster-id <id> | jq '.runtime_engine'

# Expected: "PHOTON" (12x faster SQL, 2-3x cost reduction)
```

**5.2 Use Serverless SQL for Analytics**

```
# Check SQL warehouse configuration
databricks sql warehouses get --id <warehouse-id>

# Verify: serverless=true, auto_stop_mins=10-15
```

**5.3 Optimize Delta Tables**

```
-- Z-ORDER by commonly filtered columns
OPTIMIZE <table_name> ZORDER BY (date, user_id, region);

-- Enable auto-optimize for streaming tables
ALTER TABLE <table_name> SET TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Check table statistics
DESCRIBE DETAIL <table_name>;
DESCRIBE HISTORY <table_name>;
```

**5.4 Configure Autoscaling (Performance-Optimized)**

```
{
  "autoscale": {
    "min_workers": 2,
    "max_workers": 20
  },
  "spark_conf": {
    "spark.databricks.delta.optimizeWrite.enabled": "true",
    "spark.databricks.delta.autoCompact.enabled": "true"
  }
}
```

**5.5 Enable Delta Cache**

```
# Verify Delta Cache enabled
az databricks cluster get --cluster-id <id> | jq '.spark_conf."spark.databricks.io.cache.enabled"'

# Expected: "true"
```

**5.6 Use Cluster Pools for Low Latency**

```
# Create cluster pool (reduces startup from 5-10 min to <30 sec)
databricks instance-pools create \
  --instance-pool-name "general-purpose-pool" \
  --node-type-id "Standard_DS3_v2" \
  --min-idle-instances 2 \
  --max-capacity 10 \
  --idle-instance-autotermination-minutes 15
```

**5.7 Partition Data Strategically**

```
-- Partition by date (most common filter)
CREATE TABLE IF NOT EXISTS events (
  event_id STRING,
  event_time TIMESTAMP,
  user_id STRING,
  event_type STRING
)
USING DELTA
PARTITIONED BY (DATE(event_time));

-- Avoid over-partitioning: <10,000 partitions, >1GB per partition
```

**5.8 Use Parquet with ZSTD Compression**

```python
# Write optimized format
df.write \
  .format("delta") \
  .option("compression", "zstd") \
  .partitionBy("date") \
  .mode("append") \
  .save("/mnt/data/optimized_table")
```

**5.9 Enable Adaptive Query Execution (AQE)**

```python
# Verify AQE enabled (default in Databricks Runtime 7.0+)
spark.conf.get("spark.sql.adaptive.enabled")  # Should be "true"

# Configure for optimal performance
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

---

## 6\. Unity Catalog Governance

### Agent Actions

**6.1 Verify Unity Catalog Setup**

```
-- Check metastore configuration
DESCRIBE METASTORE;

-- List all catalogs
SHOW CATALOGS;

-- Verify external locations
SHOW EXTERNAL LOCATIONS;
```

**6.2 Implement Fine-Grained Access Control**

```
-- Grant least-privilege access
GRANT SELECT ON TABLE <catalog>.<schema>.<table> TO `user@example.com`;
GRANT USAGE ON CATALOG <catalog> TO `data-analysts`;
GRANT USAGE ON SCHEMA <catalog>.<schema> TO `data-analysts`;

-- Verify permissions
SHOW GRANTS ON TABLE <catalog>.<schema>.<table>;
```

**6.3 Enable Audit Logging**

```
-- Query audit logs from system tables
SELECT 
  event_time,
  user_identity,
  action_name,
  request_params.full_name_arg as object_accessed
FROM system.access.audit
WHERE action_name IN ('getTable', 'readFiles', 'updateTable')
  AND event_time >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY event_time DESC;
```

**6.4 Configure External Locations**

```
-- Create external location with managed identity
CREATE EXTERNAL LOCATION IF NOT EXISTS prod_data
URL 'abfss://data@storageaccount.dfs.core.windows.net/prod'
WITH (STORAGE CREDENTIAL azure_managed_identity);

-- Verify access
LIST 'abfss://data@storageaccount.dfs.core.windows.net/prod';
```

**6.5 Implement Data Lineage Tracking**

```
-- Query lineage information
SELECT 
  source_table_full_name,
  target_table_full_name,
  notebook_path,
  created_at
FROM system.access.table_lineage
WHERE target_table_full_name LIKE '%production%'
ORDER BY created_at DESC;
```

---

## 7\. Monitoring & Alerting

### Agent Actions

**7.1 Configure Azure Monitor Alerts**

```
# Alert on cluster failures
az monitor metrics alert create \
  --name "databricks-cluster-failures" \
  --resource <workspace-id> \
  --condition "count clusterFailures > 5" \
  --window-size 5m \
  --action <action-group-id>

# Alert on job failures
az monitor metrics alert create \
  --name "databricks-job-failures" \
  --resource <workspace-id> \
  --condition "count jobFailures > 3" \
  --window-size 15m
```

**7.2 Query System Tables for Insights**

```
-- Cluster usage analysis
SELECT 
  cluster_id,
  cluster_name,
  SUM(usage_quantity) as total_dbus,
  COUNT(DISTINCT usage_date) as active_days
FROM system.billing.usage
WHERE usage_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY cluster_id, cluster_name
ORDER BY total_dbus DESC;

-- Failed jobs in last 24 hours
SELECT 
  job_id,
  job_name,
  run_id,
  start_time,
  error_message
FROM system.lakeflow.job_run_timeline
WHERE state = 'FAILED'
  AND start_time >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR;
```

**7.3 Set Up Workspace Health Checks**

```
# Check workspace status
az databricks workspace show --name <workspace> --query "provisioningState"

# Check cluster health
databricks clusters list | jq '.clusters[] | {id, state, state_message}'

# Check SQL warehouse status
databricks sql warehouses list | jq '.warehouses[] | {id, name, state}'
```

---

## 8\. Disaster Recovery

### Agent Actions

**8.1 Multi-Region Deployment (Mission-Critical)**

```
# Secondary region workspace
az databricks workspace create \
  --name <workspace-name>-dr \
  --location eastus2 \
  --resource-group <rg> \
  --sku premium

# Configure workspace replication (bi-directional)
databricks workspace import_dir /backups /
```

**8.2 Cross-Region Metastore Sync**

```
-- Backup Unity Catalog metadata
CREATE TABLE catalog_backup AS
SELECT * FROM system.information_schema.tables;

CREATE TABLE permissions_backup AS
SELECT * FROM system.information_schema.table_privileges;

-- Store in cross-region storage
COPY INTO 'abfss://dr@storageaccount.dfs.core.windows.net/backups/catalog/'
FROM catalog_backup;
```

**8.3 Configure Storage Replication**

```
# Enable GZRS (Geo-Zone-Redundant Storage)
az storage account update \
  --name <storage-account> \
  --sku Standard_GZRS

# Verify replication
az storage account show --name <storage-account> | jq '.sku.name'
```

---

## 9\. Serverless Recommendations

### Priority Actions for Serverless

**9.1 Migrate to Serverless SQL Warehouses**

```
# Create serverless SQL warehouse
databricks sql warehouses create \
  --name "serverless-analytics" \
  --cluster-size "2X-Small" \
  --enable-serverless-compute true \
  --auto-stop-mins 10

# Expected: 30-50% cost reduction, instant scaling
```

**9.2 Use Serverless Jobs**

```
{
  "name": "serverless-etl-job",
  "job_clusters": [{
    "job_cluster_key": "serverless-cluster",
    "new_cluster": {
      "spark_version": "13.3.x-scala2.12",
      "node_type_id": "Standard_DS3_v2",
      "num_workers": 2,
      "serverless_compute": true
    }
  }],
  "tasks": [{
    "task_key": "etl_task",
    "job_cluster_key": "serverless-cluster"
  }]
}
```

**9.3 Disable Cluster Pools (Serverless Context)**

*   ⚠️ Cluster pools incur idle infrastructure costs
*   ✅ Serverless eliminates need for pre-warmed instances
*   ✅ Startup time: \<30 seconds (comparable to pools)

---

## 10\. Agent Execution Checklist

### Daily Operations

*   Check cluster health: `databricks clusters list`
*   Review failed jobs: Query `system.lakeflow.job_run_timeline`
*   Monitor DBU consumption: Query `system.billing.usage`
*   Verify serverless SQL warehouse status
*   Check Unity Catalog audit logs

### Weekly Operations

*   Run `OPTIMIZE` on high-volume Delta tables
*   Run `VACUUM` on Delta tables (7-day retention)
*   Review cost trends in Azure Cost Management
*   Backup workspace configurations
*   Audit Unity Catalog permissions

### Monthly Operations

*   Review and right-size clusters based on usage patterns
*   Audit IP access lists and network security groups
*   Rotate customer-managed keys (if applicable)
*   Review and update compute policies
*   Test disaster recovery procedures
*   Archive old audit logs to cold storage

### Quarterly Operations

*   Review reserved capacity (DBCU) commitments
*   Conduct chaos engineering tests
*   Update IaC templates and Databricks Asset Bundles
*   Security baseline review using SAT (Security Analysis Tool)
*   Performance benchmarking and optimization review

---

## 11\. Critical Alerts

Configure these alerts for proactive management:

| Alert | Threshold | Action |
| --- | --- | --- |
| Cluster failures | \>5 in 5 min | Auto-restart, escalate |
| Job failures | \>3 in 15 min | Retry with backoff, notify team |
| DBU consumption spike | \>150% baseline | Alert cost owner, investigate |
| Workspace capacity | \>80% quota | Request quota increase |
| Storage growth | \>20% week-over-week | Audit data retention, run VACUUM |
| Unity Catalog errors | \>10 in 1 hour | Check permissions, investigate |
| SQL warehouse queue time | \>5 min | Scale up warehouse size |

---

## 12\. Security Baseline Verification

Run these checks monthly:

```
# 1. Verify VNet injection
az databricks workspace show --name <workspace> | jq '.parameters.customVirtualNetworkId'

# 2. Verify no public network access
az databricks workspace show --name <workspace> | jq '.parameters.publicNetworkAccess'

# 3. Verify Unity Catalog enabled
az databricks workspace show --name <workspace> | jq '.parameters.enableUnityMetastore'

# 4. Verify customer-managed keys
az databricks workspace show --name <workspace> | jq '.parameters.encryption'

# 5. Verify diagnostic logging enabled
az monitor diagnostic-settings list --resource <workspace-id>

# 6. Verify IP access lists configured
databricks ip-access-lists list

# 7. Verify secure cluster connectivity (no public IPs)
databricks clusters list | jq '.clusters[] | {id, enable_local_disk_encryption}'
```

---

## 13\. Quick Reference - Serverless vs. Traditional

| Feature | Serverless | Traditional Clusters | Recommendation |
| --- | --- | --- | --- |
| **Startup Time** | \<30 sec | 5-10 min | ✅ Serverless for ad-hoc |
| **Cost Model** | Per-query consumption | Always-running | ✅ Serverless for variable workloads |
| **Management** | Fully managed by Microsoft | User-managed | ✅ Serverless for reduced ops overhead |
| **Scaling** | Instant, automatic | Autoscaling (2-5 min lag) | ✅ Serverless for unpredictable loads |
| **SQL Workloads** | Photon-accelerated | Manual Photon config | ✅ Serverless SQL warehouses |
| **Batch Jobs** | Serverless Jobs | Job clusters | ✅ Serverless Jobs for intermittent runs |
| **Streaming** | Not supported | Supported | ❌ Use traditional for continuous streaming |
| **ML Training** | Not supported | GPU clusters | ❌ Use traditional for deep learning |

---

## 14\. Common Agent Queries

### Check Cluster Status

```
databricks clusters list | jq '.clusters[] | {id, name, state}'
```

### Get Recent Job Failures

```
SELECT job_id, job_name, run_id, error_message
FROM system.lakeflow.job_run_timeline
WHERE state = 'FAILED' AND start_time >= CURRENT_TIMESTAMP - INTERVAL '1' HOUR;
```

### Calculate Daily DBU Cost

```
SELECT 
  usage_date,
  SUM(usage_quantity * list_price) as estimated_cost_usd
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE
GROUP BY usage_date;
```

### Identify Large Tables

```
SELECT table_name, size_bytes / 1024 / 1024 / 1024 as size_gb
FROM system.information_schema.table_storage_metrics
WHERE size_gb > 100
ORDER BY size_gb DESC LIMIT 20;
```

### Audit Recent Data Access

```
SELECT user_identity, action_name, request_params.full_name_arg as object
FROM system.access.audit
WHERE action_name = 'readFiles' AND event_time >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY event_time DESC LIMIT 100;
```

---

## 15\. Emergency Runbook

### Workspace Unavailable

```
# 1. Check workspace status
az databricks workspace show --name <workspace> --query "provisioningState"

# 2. Check Azure service health
az rest --method get --url "https://management.azure.com/subscriptions/<sub-id>/providers/Microsoft.ResourceHealth/events?api-version=2022-10-01"

# 3. Failover to DR region (if configured)
# 4. Contact Azure Support if service issue confirmed
```

### High DBU Consumption

```
-- Identify top consumers
SELECT cluster_id, SUM(usage_quantity) as dbus
FROM system.billing.usage
WHERE usage_date = CURRENT_DATE
GROUP BY cluster_id
ORDER BY dbus DESC LIMIT 10;

-- Terminate runaway clusters
-- databricks clusters delete --cluster-id <id>
```

### Unity Catalog Access Denied

```
-- Check current permissions
SHOW GRANTS ON TABLE <catalog>.<schema>.<table>;

-- Grant required access
GRANT SELECT ON TABLE <catalog>.<schema>.<table> TO `user@example.com`;
```

---

## 16\. Key Metrics to Track

| Metric | Target | Alert Threshold | Source |
| --- | --- | --- | --- |
| Cluster startup time | \<2 min | \>5 min | Azure Monitor |
| Job success rate | \>95% | \<90% | system.lakeflow.job\_run\_timeline |
| SQL query latency (p95) | \<10 sec | \>30 sec | SQL Analytics |
| DBU cost variance | \<10% MoM | \>20% MoM | system.billing.usage |
| Delta table optimization | Daily | \>3 days | system.information\_schema.tables |
| Storage growth rate | \<15% MoM | \>30% MoM | system.information\_schema.table\_storage\_metrics |
| Unity Catalog errors | \<5/day | \>20/day | system.access.audit |

---

## 17\. References

*   [Azure Databricks Documentation](https://learn.microsoft.com/en-us/azure/databricks/)
*   [Unity Catalog Best Practices](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/best-practices)
*   [Delta Lake Optimization](https://learn.microsoft.com/en-us/azure/databricks/delta/optimize)
*   [Serverless Compute](https://learn.microsoft.com/en-us/azure/databricks/serverless-compute/)
*   [Security Analysis Tool (SAT)](https://learn.microsoft.com/en-us/azure/databricks/administration-guide/security/security-analysis-tool)

---

**Last Updated:** February 9, 2026  
**Version:** 1.0  
**Target Platform:** Azure Databricks (Serverless + Unity Catalog)