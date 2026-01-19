---
name: vertex-ai-reasoning-engine-config
description: Configure environment variables on deployed Vertex AI Reasoning Engine instances via REST API. Use when CLI tooling fails or is incomplete. Handles authentication, config merging, and token refresh automatically.
license: MIT
---

# Vertex AI Reasoning Engine Configuration Skill

## Overview

This skill solves the problem of incomplete Google Cloud CLI tooling by providing a production-ready REST API implementation for configuring environment variables on Vertex AI Reasoning Engine instances.

**Use when**: You need to configure environment variables (logging, observability, telemetry) on a deployed Vertex AI Reasoning Engine and CLI commands fail or don't expose the necessary fields.

## Quick Start

### Using the Python Script

```bash
python vertex_ai_reasoning_config.py \
  --project-id my-gcp-project \
  --location us-central1 \
  --engine-id my-engine-123 \
  --env-vars LOG_LEVEL=debug TRACE_ENABLED=true
```

### In Claude Desktop

1. Install this skill from the skill gallery
2. Reference in any prompt: "Configure my Reasoning Engine with LOG_LEVEL=debug and TRACE_ENABLED=true"
3. Claude will automatically validate prerequisites, retrieve current config, merge variables, and apply via REST API

### In n8n Workflows

```json
{
  "type": "executeCommand",
  "command": "python /path/to/vertex_ai_reasoning_config.py --project-id {{$json.projectId}} --location {{$json.location}} --engine-id {{$json.engineId}} --env-vars LOG_LEVEL=debug"
}
```

## The Problem

Google Cloud's CLI tooling (`gcloud`) doesn't expose all Vertex AI Reasoning Engine configuration fields. Multiple CLI approaches fail with unclear errors:

| Approach | Result |
|----------|--------|
| `gcloud beta vertex ai reasoning-engines update` | ❌ Command not found |
| `gcloud alpha vertex ai reasoning-engines update` | ❌ Command not found |
| `gcloud vertex ai reasoning-engines update` | ❌ Missing field support |
| REST API with `environmentVariables` field | ❌ Unknown field |
| REST API with `env` at root level | ❌ Unknown field |

## The Solution

Configure via direct REST API PATCH using the field path `spec.deploymentSpec.env` with an `updateMask` parameter.

### Correct Approach

```
PATCH /v1beta1/projects/{PROJECT}/locations/{REGION}/reasoningEngines/{ENGINE_ID}?updateMask=spec.deploymentSpec.env

Headers:
  Authorization: Bearer {TOKEN}
  Content-Type: application/json

Body:
{"spec": {"deploymentSpec": {"env": [{"name": "KEY", "value": "value"}]}}}
```

### Discovery Process

1. Started with CLI assumptions → CLI failed
2. Examined actual API responses via GET request
3. Inspected JSON structure to find env field location
4. Tested REST API with various field names
5. Discovered `spec.deploymentSpec.env` through response exploration
6. Identified `updateMask` requirement through API errors
7. Validated full env array must be provided (discovered when PATCH deleted variables)

**Key Learning**: When CLI fails, inspect actual API responses and test REST API directly.

## Critical Gotchas

### 🔴 CRITICAL: Full Environment Array Required

PATCH replaces the entire env array, not individual fields. **You must include ALL existing variables plus new ones.**

The provided Python script handles this automatically by:
1. Retrieving current configuration via GET
2. Extracting existing `spec.deploymentSpec.env` array
3. Merging new variables with existing ones
4. Sending complete merged array in PATCH

**Manual workaround if not using the script**:
```bash
# 1. Get current config
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT_ID/locations/us-central1/reasoningEngines/ENGINE_ID \
  > current.json

# 2. Extract env array, merge new vars, update current.json

# 3. PATCH with merged array
curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" -d @current.json \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT_ID/locations/us-central1/reasoningEngines/ENGINE_ID?updateMask=spec.deploymentSpec.env"
```

### 🟡 Exact Field Path (camelCase)

Must use `spec.deploymentSpec.env` (NOT `spec.deployment_spec.env` or `spec.deployment_spec.env`). Case matters.

### 🟡 updateMask is Essential

Always include `?updateMask=spec.deploymentSpec.env` to restrict changes to only the env field and prevent accidentally resetting other configuration.

### 🟡 Access Token Expiration

Tokens from `gcloud auth print-access-token` expire in 1 hour. The Python script automatically:
- Caches tokens for up to 50 minutes
- Detects expiration
- Refreshes when needed
- Retries operations after refresh

## Common Use Cases

| Scenario | Environment Variables |
|----------|----------------------|
| Enable debug logging | `LOG_LEVEL=debug`, `DEBUG_MODE=true` |
| Configure observability | `OTEL_ENDPOINT=http://collector:4317`, `TRACE_ENABLED=true` |
| Custom telemetry | `TELEMETRY_ENDPOINT=custom`, `SAMPLING_RATE=0.1` |
| Troubleshooting | `VERBOSE_OUTPUT=true`, `REQUEST_LOGGING=true` |

## Prerequisites

- ✅ `gcloud` CLI installed and authenticated
- ✅ `curl` installed
- ✅ Access to a deployed Vertex AI Reasoning Engine
- ✅ Google Cloud credentials with Vertex AI API permissions

### Verify Prerequisites

```bash
gcloud auth list                                    # Check auth
gcloud config get-value project                    # Check project
gcloud ai reasoning-engines list --location=us-central1  # List engines
```

## Rollback Procedure

If bad environment variables are set:

```bash
# 1. Capture current state (before you made changes)
gcloud auth print-access-token > token.txt
curl -H "Authorization: Bearer $(cat token.txt)" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT_ID/locations/us-central1/reasoningEngines/ENGINE_ID \
  > backup.json

# 2. Edit backup.json to restore original env values

# 3. PATCH to restore
curl -X PATCH \
  -H "Authorization: Bearer $(cat token.txt)" \
  -H "Content-Type: application/json" \
  -d @backup.json \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT_ID/locations/us-central1/reasoningEngines/ENGINE_ID?updateMask=spec.deploymentSpec.env"

# Note: Changes take effect immediately; no restart needed
```

## Integration Points

- **CLI**: Direct command-line execution
- **Claude Desktop**: One-click install, automatic agent discovery
- **n8n Workflows**: Execute command nodes with parameter mapping
- **Google ADK Agents**: Import Python module, call functions directly
- **Shell Scripts**: Subprocess calls with JSON result parsing
- **CI/CD Pipelines**: GitHub Actions or Cloud Build integration

## Files & Components

This skill includes:

- `scripts/vertex_ai_reasoning_config.py` - Main executable with:
  - Prerequisite validation
  - Token refresh logic
  - Config merging
  - Comprehensive error messages
  
- `references/api-response-example.json` - Sample API response for understanding structure
- `references/failure-modes.md` - Detailed failure path documentation
- `QUICK_REFERENCE.md` - Quick lookup guide for common tasks

## Acceptance Criteria

- ✅ Retrieve current Reasoning Engine configuration
- ✅ Update environment variables via REST API
- ✅ Verify variables appear in response within 5 seconds
- ✅ No unintended configuration changes
- ✅ Handle multiple variable sets
- ✅ Preserve existing environment variables (no deletion)
- ✅ Automatic token refresh
- ✅ Comprehensive error messages

## Error Handling & Debugging

### Enable Verbose Logging

```bash
python vertex_ai_reasoning_config.py [...] --verbose
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "No active gcloud authentication" | Not logged in | `gcloud auth login` |
| "Cannot access project" | Wrong project or no permissions | `gcloud config set project PROJECT_ID` |
| "Reasoning Engine not found" | Wrong ID or location | List engines with `gcloud ai reasoning-engines list` |
| "Unknown field xyz" | Wrong field path/name | Use `spec.deploymentSpec.env` |
| "Failed to get access token" | gcloud not installed or in PATH | Install/verify gcloud CLI |

## Google Cloud References

- [Vertex AI Reasoning Engine PATCH API](https://cloud.google.com/vertex-ai/docs/reference/rest/v1beta1/projects.locations.reasoningEngines/patch)
- [Vertex AI Reasoning Engine Overview](https://cloud.google.com/vertex-ai/docs/reasoning-engine/overview)
- [Reasoning Engine Resource Definition](https://cloud.google.com/vertex-ai/docs/reference/rest/v1beta1/projects.locations.reasoningEngines#resource:-reasoningengine)

## Decision Tree: When to Use This Skill

```
Need to configure a Vertex AI Reasoning Engine?
│
├─ Q1: Can gcloud help text describe the change?
│   ├─ YES (e.g., labels, zones)
│   │  └─ Try gcloud first; fall back to this skill if it fails
│   │
│   └─ NO (e.g., deploymentSpec, nested fields)
│      └─ Use this skill (REST API method)
│
└─ This skill uses REST API PATCH with spec.deploymentSpec.env
```

## What Success Looks Like

✅ Script validates all prerequisites  
✅ Retrieves current engine configuration  
✅ Merges new variables with existing ones  
✅ Applies changes via REST API PATCH  
✅ Returns updated resource JSON  
✅ Changes visible within 5 seconds  
✅ No other config fields affected  

---

**Status**: Production Ready (v1.0.0)  
**Created**: 2025-01-19  
**Author**: Kurt Anderson  
**Last Updated**: 2025-01-19  
**License**: MIT
