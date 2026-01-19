# Failure Modes & Troubleshooting

## Failed Approaches

### 1. gcloud beta vertex ai reasoning-engines update
**Command**: `gcloud beta vertex ai reasoning-engines update --id=ENGINE_ID --update-mask=spec.deploymentSpec.env --location=us-central1`

**Error**: `ERROR: (gcloud.beta.vertex.ai.reasoning-engines.update) unrecognized arguments: ...` or "No module named 'reasoning-engines'"

**Reason**: Beta tooling for Vertex AI Reasoning Engines doesn't exist or is incomplete.

**Search Keywords**: gcloud beta vertex ai reasoning-engines, vertex ai beta update

---

### 2. gcloud alpha vertex ai reasoning-engines update
**Command**: `gcloud alpha vertex ai reasoning-engines update --id=ENGINE_ID --location=us-central1`

**Error**: Similar to above; command not found or invalid arguments

**Reason**: Alpha tooling also doesn't expose the necessary fields.

**Search Keywords**: gcloud alpha reasoning-engines, vertex ai alpha update

---

### 3. gcloud vertex ai reasoning-engines update (Stable)
**Command**: `gcloud vertex ai reasoning-engines update RESOURCE_NAME --location=us-central1 --update-mask=spec.deploymentSpec.env`

**Error**: `ERROR: Missing required components: [spec.deploymentSpec.env]` or argument parsing errors

**Reason**: Stable gcloud command exists but doesn't support all fields needed for full configuration.

**Search Keywords**: gcloud vertex ai reasoning-engines update missing components

---

### 4. REST API with environmentVariables field
**Endpoint**: `PATCH /v1beta1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}`

**Request Body**:
```json
{
  "environmentVariables": [
    {"name": "LOG_LEVEL", "value": "debug"}
  ]
}
```

**Error**: `"error": {"code": 400, "message": "Invalid request: Field 'environmentVariables' not recognized"}`

**Reason**: Field name is completely incorrect; the API doesn't have an `environmentVariables` field at all.

**Search Keywords**: vertex ai reasoning engine environmentVariables unknown field, REST API field name

---

### 5. REST API with env at Root Level
**Endpoint**: `PATCH /v1beta1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}`

**Request Body**:
```json
{
  "env": [
    {"name": "LOG_LEVEL", "value": "debug"}
  ]
}
```

**Error**: `"error": {"code": 400, "message": "Invalid request: Field 'env' not recognized"}`

**Reason**: Field exists but must be nested under `spec.deploymentSpec`, not at root level.

**Search Keywords**: vertex ai reasoning engine env field not found, spec nesting

---

### 6. Incorrect Nesting: spec.env (Missing deploymentSpec)
**Request Body**:
```json
{
  "spec": {
    "env": [
      {"name": "LOG_LEVEL", "value": "debug"}
    ]
  }
}
```

**Error**: `"error": {"code": 400, "message": "Invalid request: Field 'env' not recognized"}`

**Reason**: The field is `spec.deploymentSpec.env`, not `spec.env`. The intermediate `deploymentSpec` level is required.

**Search Keywords**: spec.env not recognized, deploymentSpec path structure

---

### 7. Wrong Case: spec.deployment_spec.env (snake_case)
**Request Body**:
```json
{
  "spec": {
    "deployment_spec": {
      "env": [...]
    }
  }
}
```

**Error**: `"error": {"code": 400, "message": "Invalid request: Field 'deployment_spec' not recognized"}`

**Reason**: Must use camelCase `deploymentSpec`, not snake_case `deployment_spec`. Google APIs use camelCase.

**Search Keywords**: deployment_spec vs deploymentSpec, api field case sensitivity

---

## The Correct Path

**Request Body**:
```json
{
  "spec": {
    "deploymentSpec": {
      "env": [
        {"name": "LOG_LEVEL", "value": "debug"},
        {"name": "TRACE_ENABLED", "value": "true"}
      ]
    }
  }
}
```

**Endpoint**: `PATCH /v1beta1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}?updateMask=spec.deploymentSpec.env`

**Headers**:
```
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json
```

**Response**: 200 OK with updated ReasoningEngine resource

---

## Common Pitfalls

### Pitfall 1: Not Providing Full Environment Array
**Symptom**: All existing environment variables disappear after PATCH

**Cause**: PATCH replaces the entire array; must include existing variables plus new ones

**Solution**: Retrieve current config via GET first, extract env array, merge with new vars, then PATCH

```bash
# GET current config
curl -H "Authorization: Bearer $TOKEN" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT/locations/us-central1/reasoningEngines/ENGINE > current.json

# Merge vars in current.json, then:
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @current.json \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/PROJECT/locations/us-central1/reasoningEngines/ENGINE?updateMask=spec.deploymentSpec.env"
```

---

### Pitfall 2: Missing updateMask Parameter
**Symptom**: Other Reasoning Engine fields get reset unexpectedly

**Cause**: Without `updateMask`, PATCH might affect more fields than intended

**Solution**: Always include `?updateMask=spec.deploymentSpec.env` in the URL

```bash
# WRONG - might reset other fields
curl -X PATCH ... "https://...reasoningEngines/ENGINE"

# CORRECT - only updates env
curl -X PATCH ... "https://...reasoningEngines/ENGINE?updateMask=spec.deploymentSpec.env"
```

---

### Pitfall 3: Token Expired (1-Hour Limit)
**Symptom**: Request fails with 401 Unauthorized after running for >1 hour

**Cause**: Tokens from `gcloud auth print-access-token` expire in 1 hour

**Solution**: Refresh token before making request, or use automatic refresh logic in long-running scripts

```bash
# Refresh token before request
gcloud auth print-access-token > /tmp/token.txt
TOKEN=$(cat /tmp/token.txt)
curl -H "Authorization: Bearer $TOKEN" ...
```

---

## Discovery Timeline

1. **Start**: Assume CLI (`gcloud`) should work → Try beta/alpha versions
2. **Realize**: CLI tooling is incomplete → Switch to REST API
3. **Try**: Common field names (`environmentVariables`, `env`) → All fail
4. **GET**: Current resource to see actual structure → Discover `spec.deploymentSpec.env`
5. **Test**: PATCH with field path → Works!
6. **Discover**: Without `updateMask`, other fields affected → Add query parameter
7. **Warning**: All existing vars deleted after PATCH → Learn array must be complete
8. **Solution**: GET-merge-PATCH workflow → Reliable approach

---

## Prevention: How to Avoid These Issues

1. **Always GET first** - Inspect actual API response structure
2. **Follow Google API naming conventions** - camelCase for nested objects
3. **Use updateMask** - Restrict changes to target fields only
4. **Preserve existing values** - PATCH replaces arrays, not merges
5. **Test on non-production engines first** - Validate approach before production
6. **Keep backups** - Save current config before making changes
7. **Handle token refresh** - Plan for 1-hour expiration in long-running operations

---

## Quick Lookup: Error Message → Solution

| Error Contains | Try This |
|----------------|----------|
| "unrecognized arguments" | CLI tooling missing; use REST API |
| "Unknown field" | Check field name and nesting path |
| "Field not recognized" | Verify camelCase (e.g., `deploymentSpec` not `deployment_spec`) |
| "Missing required components" | CLI doesn't support this field; use REST API |
| "401 Unauthorized" | Refresh access token; 1-hour expiration |
| "Variables disappeared" | PATCH requires full env array; retrieve current config first |
| "Other fields affected" | Add `?updateMask=spec.deploymentSpec.env` to URL |

