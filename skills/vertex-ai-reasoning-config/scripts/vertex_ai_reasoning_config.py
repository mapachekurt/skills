#!/usr/bin/env python3
"""
Vertex AI Reasoning Engine Environment Configuration Tool
Skill: Configure Vertex AI Reasoning Engine Telemetry & Logging

Usage:
    python vertex_ai_reasoning_config.py \
        --project-id YOUR_PROJECT \
        --location us-central1 \
        --engine-id ENGINE_123 \
        --env-vars LOG_LEVEL=debug TRACE_ENABLED=true

Returns:
    JSON response with operation status and updated resource
"""

import json
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlencode

@dataclass
class EnvVar:
    """Represents a single environment variable"""
    name: str
    value: str

class VertexAIReasoningEngineConfig:
    """
    Configures Vertex AI Reasoning Engine environment variables via REST API.
    
    Key Design:
    - Uses REST API (not gcloud CLI) because CLI doesn't expose deploymentSpec fields
    - Automatically retrieves current env vars, merges with new ones
    - Handles token refresh transparently
    - Validates all prerequisite conditions
    """
    
    API_BASE = "aiplatform.googleapis.com"
    API_VERSION = "v1beta1"
    
    def __init__(self, project_id: str, location: str, engine_id: str, verbose: bool = False):
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id
        self.verbose = verbose
        self._access_token: Optional[str] = None
        self._token_refreshed_at: int = 0
    
    def log(self, message: str):
        """Print verbose logging"""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def error(self, message: str):
        """Print error message"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def _get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get Google Cloud access token.
        
        Caches token for up to 50 minutes (tokens valid 1 hour, refresh at 50min).
        """
        current_time = int(time.time())
        
        # Refresh if forced, doesn't exist, or older than 50 minutes
        if not force_refresh and self._access_token and (current_time - self._token_refreshed_at) < 3000:
            self.log(f"Using cached token (refreshed {current_time - self._token_refreshed_at}s ago)")
            return self._access_token
        
        self.log("Refreshing Google Cloud access token...")
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
            self._access_token = result.stdout.strip()
            self._token_refreshed_at = current_time
            self.log("Access token refreshed successfully")
            return self._access_token
        except subprocess.CalledProcessError as e:
            self.error(f"Failed to get access token: {e.stderr}")
            raise
    
    def _build_url(self, query_params: Optional[Dict] = None) -> str:
        """Build full REST API URL"""
        base_url = (
            f"https://{self.location}-{self.API_BASE}/"
            f"{self.API_VERSION}/"
            f"projects/{self.project_id}/"
            f"locations/{self.location}/"
            f"reasoningEngines/{self.engine_id}"
        )
        
        if query_params:
            base_url += f"?{urlencode(query_params)}"
        
        return base_url
    
    def get_current_config(self) -> Dict:
        """
        GET current Reasoning Engine configuration.
        
        CRITICAL: Fetch existing env vars before PATCH to avoid deleting them.
        """
        self.log("Fetching current Reasoning Engine configuration...")
        
        url = self._build_url()
        token = self._get_access_token()
        
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X", "GET",
                    "-H", f"Authorization: Bearer {token}",
                    "-H", "Content-Type: application/json",
                    url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            config = json.loads(result.stdout)
            self.log(f"Successfully retrieved config: {json.dumps(config, indent=2)}")
            return config
            
        except subprocess.CalledProcessError as e:
            self.error(f"Failed to GET configuration: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            self.error(f"Invalid JSON response: {e}")
            self.error(f"Response: {result.stdout}")
            raise
    
    def _merge_env_vars(self, current_config: Dict, new_vars: List[EnvVar]) -> List[Dict]:
        """
        Merge new environment variables with existing ones.
        
        GOTCHA: PATCH replaces entire env array, so must preserve existing vars.
        """
        # Extract current env array
        current_env = current_config.get("spec", {}).get("deploymentSpec", {}).get("env", [])
        self.log(f"Current env vars: {current_env}")
        
        # Build dict of existing vars for easy lookup
        env_dict = {var["name"]: var["value"] for var in current_env}
        
        # Merge with new vars (new vars override existing)
        for new_var in new_vars:
            env_dict[new_var.name] = new_var.value
            self.log(f"Setting {new_var.name}={new_var.value}")
        
        # Convert back to list format
        merged = [{"name": k, "value": v} for k, v in env_dict.items()]
        self.log(f"Merged env vars: {merged}")
        
        return merged
    
    def update_env_vars(self, new_vars: List[EnvVar]) -> Dict:
        """
        Update environment variables via REST API PATCH.
        
        CRITICAL: Uses updateMask to restrict change scope to env field only.
        """
        self.log(f"Updating {len(new_vars)} environment variable(s)...")
        
        # Step 1: Get current config
        current_config = self.get_current_config()
        
        # Step 2: Merge env vars
        merged_env = self._merge_env_vars(current_config, new_vars)
        
        # Step 3: Build PATCH request body
        patch_body = {
            "spec": {
                "deploymentSpec": {
                    "env": merged_env
                }
            }
        }
        
        self.log(f"PATCH body: {json.dumps(patch_body, indent=2)}")
        
        # Step 4: Execute PATCH with updateMask
        url = self._build_url({"updateMask": "spec.deploymentSpec.env"})
        token = self._get_access_token()
        
        try:
            # Write body to temp file to avoid shell escaping issues
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(patch_body, f)
                body_file = f.name
            
            self.log(f"Executing PATCH to {url}")
            
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X", "PATCH",
                    "-H", f"Authorization: Bearer {token}",
                    "-H", "Content-Type: application/json",
                    "-d", f"@{body_file}",
                    url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            response = json.loads(result.stdout)
            
            # Clean up temp file
            import os
            os.unlink(body_file)
            
            self.log(f"PATCH successful: {json.dumps(response, indent=2)}")
            return response
            
        except subprocess.CalledProcessError as e:
            self.error(f"PATCH failed: {e.stderr}")
            # Try to parse error as JSON
            try:
                error_data = json.loads(e.stderr)
                self.error(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            raise
        except json.JSONDecodeError as e:
            self.error(f"Invalid JSON response: {e}")
            self.error(f"Response: {result.stdout}")
            raise
    
    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        """Validate all prerequisites before attempting configuration"""
        errors = []
        
        # Check gcloud installed
        result = subprocess.run(["which", "gcloud"], capture_output=True)
        if result.returncode != 0:
            errors.append("gcloud CLI not found in PATH")
        
        # Check curl installed
        result = subprocess.run(["which", "curl"], capture_output=True)
        if result.returncode != 0:
            errors.append("curl not found in PATH")
        
        # Check authentication
        result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, text=True)
        if "ACTIVE" not in result.stdout:
            errors.append("No active gcloud authentication")
        
        # Check project access
        result = subprocess.run(
            ["gcloud", "projects", "describe", self.project_id],
            capture_output=True
        )
        if result.returncode != 0:
            errors.append(f"Cannot access project {self.project_id}")
        
        # Check reasoning engine exists
        result = subprocess.run(
            [
                "gcloud", "ai", "reasoning-engines", "list",
                f"--project={self.project_id}",
                f"--location={self.location}",
                "--format=value(id)"
            ],
            capture_output=True,
            text=True
        )
        
        if self.engine_id not in result.stdout:
            errors.append(
                f"Reasoning Engine {self.engine_id} not found in {self.location}. "
                f"Available: {result.stdout.strip()}"
            )
        
        return len(errors) == 0, errors


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Configure Vertex AI Reasoning Engine environment variables"
    )
    parser.add_argument("--project-id", required=True, help="Google Cloud project ID")
    parser.add_argument("--location", required=True, help="Engine location (e.g., us-central1)")
    parser.add_argument("--engine-id", required=True, help="Reasoning Engine ID")
    parser.add_argument(
        "--env-vars",
        nargs="+",
        help="Environment variables in KEY=VALUE format",
        default=[]
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Parse env vars
    env_vars = []
    for var in args.env_vars:
        if "=" not in var:
            print(f"ERROR: Invalid env var format: {var} (must be KEY=VALUE)", file=sys.stderr)
            sys.exit(1)
        key, value = var.split("=", 1)
        env_vars.append(EnvVar(name=key, value=value))
    
    # Create configurator
    configurator = VertexAIReasoningEngineConfig(
        project_id=args.project_id,
        location=args.location,
        engine_id=args.engine_id,
        verbose=args.verbose
    )
    
    # Validate prerequisites
    print("Validating prerequisites...")
    valid, errors = configurator.validate_prerequisites()
    if not valid:
        print("Prerequisites validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    print("✓ All prerequisites met")
    
    # Update env vars
    try:
        result = configurator.update_env_vars(env_vars)
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
