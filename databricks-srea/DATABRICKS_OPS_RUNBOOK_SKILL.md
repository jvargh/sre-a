---
name: Databricks_OPS_Runbook
description: Augments Databricks_MCP_Agent with operational incident management, audit logging, escalation, and change documentation for on-call team operations.
---

# Databricks OPS Runbook Skill

## Purpose
Transform the Databricks_MCP_Agent from diagnosis-only to full incident management. This skill adds operational workflows for incident tracking, remediation documentation, compliance auditing, and escalation.

## Capability 1: Incident Timeline Tracking

### Workflow
1. **Incident Start**: Log timestamp, incident type (failure/deprecation/compliance), reported by
2. **Investigation Phase**: Log each discovery, tool call, evidence collected
3. **RCA Phase**: Log confidence level, root cause determination, decision points
4. **Remediation Phase**: Log each fix applied, command executed, result
5. **Closure**: Log resolution timestamp, impact analysis, lessons learned

### Output Format
```
INCIDENT TIMELINE
================
ID: <incident-id>
Reported: <timestamp>
Reporter: <user>
Type: <job-failure|validation-gap|security-finding>
Status: <investigating|resolved|escalated>

Timeline:
- [HH:MM:SS] DISCOVER: Found 3 jobs, 1 with failed run
- [HH:MM:SS] FETCH: Retrieved run output; error: "NullPointerException"
- [HH:MM:SS] ANALYZE: Read notebook code; identified line 42 as root cause
- [HH:MM:SS] RCA: Timeout + no retries + unparsed JSON input → HIGH confidence
- [HH:MM:SS] REMEDIATE: Applied max_retries=3, timeout=3600
- [HH:MM:SS] VERIFY: Re-ran job; SUCCESS
- [HH:MM:SS] CLOSE: Incident resolved; estimated MTTR=15min

```

## Capability 2: Change Documentation & Runbook Generation

### Workflow
For each remediation step, auto-generate a runbook entry that on-call teams can follow:

### Output Format
```
RUNBOOK ENTRY
=============
Title: Fix Job Retry Policies – daily-etl
Created: <timestamp>
Incident ID: <incident-id>
RCA Summary: Job "daily-etl" failed due to no retry policy; transient workload error → no automatic recovery.

Remediation Steps (copy-paste ready):

1. Update job configuration:
   curl -X POST https://<workspace-url>/api/2.1/jobs/reset \
     -H "Authorization: Bearer <token>" \
     -d '{
       "job_id": 360515640572923,
       "new_settings": {
         "max_retries": 3,
         "min_retry_interval_millis": 120000,
         "retry_on_timeout": true,
         "timeout_seconds": 3600
       }
     }'

2. Validate fix:
   databricks jobs get --job-id 360515640572923 | jq '.settings.max_retries'
   # Expected: 3

3. Test (optional, run once):
   databricks jobs run-now --job-id 360515640572923

4. Monitor next 3 runs for success.

Rollback (if needed):
- Set max_retries back to 0, retry_on_timeout to false.

Escalation: If still failing after 3 retries, escalate to Databricks support with run_id and error message.
```

## Capability 3: Escalation Triggers

### Trigger Conditions
- **Confidence LOW**: Missing run output or code evidence → escalate to on-call with "need manual investigation"
- **PARTIAL Checks >50%**: More than half of best-practice checks are PARTIAL → escalate with "environment assessment incomplete"
- **High-severity findings**: Security FAIL (Unity Catalog disabled, no encryption) → escalate immediately
- **Recurring issue**: Same RCA root cause appears 3+ times in 7 days → escalate with pattern alert
- **Evidence unavailable**: Run output, notebook code, or SQL cannot be retrieved → escalate with access/API issue note

### Output Format
```
ESCALATION ALERT
================
Severity: <LOW|MEDIUM|HIGH|CRITICAL>
Trigger: <missing-evidence|partial-checks|security-finding|recurring|access-issue>
Escalate To: <on-call-slack-channel|email-group|pagerduty-service>

Message:
-------
[MEDIUM] Investigation blocked: Cannot retrieve run output for job run_id=236083407514246.
Possible causes: Run expired, API permission, workspace access.
Action: On-call to verify MCP token and workspace connectivity; check run retention settings.
Incident ID: <incident-id>
```

## Capability 4: Compliance Audit Logs

### Logged Data
- **Who**: User/agent that triggered investigation
- **What**: Incident details (job, resource, error)
- **When**: Timestamp (UTC)
- **Where**: Workspace ID, resource IDs
- **Why**: Incident type (failure, validation, security)
- **How**: Remediation applied, changes made

### Output Format
```
AUDIT LOG ENTRY
===============
Timestamp: 2026-02-11T12:36:00Z
Actor: agent:databricks_mcp_agent
Action: [INVESTIGATE, RCA, REMEDIATE, VALIDATE]
Resource: job_id=360515640572923, workspace_id=7405612783315468
Incident: job_failure_timeouts_without_retries
FindingConfidence: HIGH
RemediationApplied: {max_retries: 3, timeout_seconds: 3600}
ComplianceImpact: Reliability category moved from FAIL to PASS
Status: COMPLETE
```

## Capability 5: Recurring Issue Detection

### Workflow
1. **Track**: Store each RCA root cause with timestamp, job/resource, confidence
2. **Detect**: If same root cause appears 3+ times in 7 days, flag as recurring
3. **Recommend**: Suggest preventive policy or permanent fix
4. **Report**: Include in weekly SRE digest

### Output Format
```
RECURRING ISSUE ALERT
=====================
Root Cause: Job retry policies not configured (max_retries=0)
Occurrences: 3 incidents in 7 days (daily-etl, hourly-sync, nightly-backup)
Pattern: All affected jobs are Serverless, all have no retry policy
Confidence: HIGH

Preventive Action Recommended:
- Add compute policy to enforce max_retries >= 3 for all job clusters
- Add validation to on-job-create: fail if max_retries < 1 AND timeout_seconds == 0
- Add scheduled compliance check (daily) to flag jobs with no retry policy

Policy Template:
{
  "policy_name": "reliability-enforce-retries",
  "definition": {
    "max_retries": {
      "type": "range",
      "minValue": 1,
      "maxValue": 10,
      "defaultValue": 3
    },
    "timeout_seconds": {
      "type": "fixed",
      "value": 3600
    }
  }
}

Cost Impact: No additional cost; improves MTTR by ~60% for transient failures.
```

## Integration with Databricks_MCP_Agent

### Enable Section
Set `enable_skills: true` in Databricks_MCP_Agent.yaml, then reference this skill:

```yaml
skills:
  - Databricks_OPS_Runbook  # Adds timeline, runbook, escalation, audit, recurring detection
```

### Trigger Point
After RCA is complete and before returning final response:

```
Step 4b - Operational Logging (if skill enabled):
  - Capture incident timeline with all timestamps
  - Generate runbook entry for remediation steps
  - Evaluate escalation triggers; if triggered, add alert
  - Log audit entry with actor, action, resource, compliance impact
  - Scan incident history for recurring root causes; flag if 3+ in 7 days
```

## Output Intent
- **For On-Call**: Runbook entries are copy-paste ready, no ambiguity
- **For Auditors**: Audit logs tied to incidents, full traceability
- **For SREs**: Timeline + recurring detection for trend analysis and capacity planning
- **For Escalation**: Clear trigger conditions, severity levels, and next actions

