import json
import os
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools"

class ToolsBridge:
    def __init__(self):
        self.tools_registry = {}  # {tool_name: {schema, url, path, method}}
        self._load_tools()

    def _load_tools(self):
        """
        Scans the tools directory and loads OpenAPI schemas.
        Converts them into internal registry for easy execution.
        """
        if not TOOLS_DIR.exists():
            print(f"Tools directory not found: {TOOLS_DIR}")
            return

        for tool_dir in TOOLS_DIR.iterdir():
            if tool_dir.is_dir():
                schema_path = tool_dir / "schema.json"
                if schema_path.exists():
                    try:
                        with open(schema_path, "r") as f:
                            openapi_spec = json.load(f)
                            self._register_tool(tool_dir.name, openapi_spec)
                    except Exception as e:
                        print(f"Error loading schema for {tool_dir.name}: {e}")

    def _register_tool(self, tool_name: str, spec: Dict[str, Any]):
        """
        Parses OpenAPI spec to register the tool.
        Assumes 1 primary operation per schema for simplicity in this bridge V1.
        """
        try:
            # 1. Get Base URL
            base_url = spec.get("servers", [{}])[0].get("url")
            if not base_url:
                print(f"No server URL found for {tool_name}")
                return

            # 2. Find the first valid POST operation
            for path_key, path_item in spec.get("paths", {}).items():
                for method, op in path_item.items():
                    if method.lower() == "post":
                        # We found our candidate
                        operation_id = op.get("operationId", f"{tool_name}_execute")
                        description = op.get("description") or op.get("summary") or f"Execute {tool_name}"
                        
                        # Extract Request Body Schema for OpenAI function definition
                        req_body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                        
                        # Resolve $ref if top-level is a ref
                        if "$ref" in req_body:
                            ref_name = req_body["$ref"].split("/")[-1]
                            req_body = spec.get("components", {}).get("schemas", {}).get(ref_name, {})

                        # If schema has 'properties' but missing 'type': 'object', add it
                        if "properties" in req_body and "type" not in req_body:
                            req_body["type"] = "object"

                        # Register
                        self.tools_registry[tool_name] = {
                            "name": tool_name,
                            "operation_id": operation_id,
                            "description": description,
                            "url": base_url + path_key,
                            "method": "POST",
                            "parameters": req_body,
                            "spec": spec  # Keep full spec just in case
                        }
                        return # Only register one main endpoint per tool folder for now
        except Exception as e:
            print(f"Failed to parse spec for {tool_name}: {e}")

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """
        Returns the list of tools in OpenAI format.
        """
        openai_tools = []
        for name, tool in self.tools_registry.items():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"][:1024], # Truncate if too long
                    "parameters": tool["parameters"]
                }
            })
        return openai_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the tool via HTTP request to the GCP endpoint.
        """
        tool = self.tools_registry.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found."}

        url = tool["url"]
        print(f"Executing Tool: {tool_name} at {url}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=arguments)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP Error {e.response.status_code}", 
                "details": e.response.text
            }
        except Exception as e:
             return {"error": f"Execution failed: {str(e)}"}

# Global instance
tools_bridge = ToolsBridge()
