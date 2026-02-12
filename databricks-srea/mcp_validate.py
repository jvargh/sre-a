import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


def _parse_sse_json(text: str) -> Dict[str, Any]:
    if "data: " not in text:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Response was not JSON or SSE") from exc

    for line in text.split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:].strip())

    raise ValueError("No JSON data lines found in SSE response")


class MCPClient:
    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/mcp"
        self.session_id: Optional[str] = None
        self.request_id = 0
        self.timeout = timeout

    def _request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.request_id += 1
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        if not self.session_id and "Mcp-Session-Id" in response.headers:
            self.session_id = response.headers["Mcp-Session-Id"]

        return _parse_sse_json(response.text)

    def initialize(self) -> Dict[str, Any]:
        return self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-validate", "version": "1.0"},
            },
        )

    def list_tools(self) -> Dict[str, Any]:
        return self._request("tools/list")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("tools/call", {"name": name, "arguments": arguments})


def _print_tools(result: Dict[str, Any]) -> None:
    tools = result.get("result", {}).get("tools", [])
    print(f"Tools available: {len(tools)}")
    for tool in tools[:10]:
        desc = tool.get("description", "")
        short = desc[:80] + ("..." if len(desc) > 80 else "")
        print(f"- {tool.get('name', '')}: {short}")


def _print_tool_result(result: Dict[str, Any]) -> None:
    if "result" in result and "content" in result["result"]:
        for item in result["result"]["content"]:
            if item.get("type") == "text" and item.get("text"):
                text = item["text"]
                try:
                    data = json.loads(text)
                    print(json.dumps(data, indent=2)[:800])
                except json.JSONDecodeError:
                    print(text[:800])
    else:
        print(json.dumps(result, indent=2)[:800])


def _pick_tool(tools: list[Dict[str, Any]], candidates: list[str]) -> str:
    available = {tool.get("name", "") for tool in tools}
    for name in candidates:
        if name in available:
            return name
    return ""


def _find_tool_with_keyword(tools: list[Dict[str, Any]], keyword: str) -> str:
    for tool in tools:
        name = tool.get("name", "")
        if keyword in name:
            return name
    return ""


def run_initialize(client: MCPClient) -> None:
    result = client.initialize()
    print(json.dumps(result, indent=2)[:800])


def run_list_tools(client: MCPClient) -> None:
    client.initialize()
    result = client.list_tools()
    _print_tools(result)


def run_discover(client: MCPClient) -> None:
    client.initialize()
    result = client.list_tools()
    tools = result.get("result", {}).get("tools", [])
    print(f"Found {len(tools)} tools")
    for tool in tools:
        print(f"- {tool.get('name', '')}")


def run_validation(client: MCPClient, warehouse_id: Optional[str]) -> None:
    client.initialize()
    tools_result = client.list_tools()
    tools = tools_result.get("result", {}).get("tools", [])

    print("Test: list_clusters")
    _print_tool_result(client.call_tool("list_clusters", {}))

    warehouse_tool = _pick_tool(
        tools,
        [
            "list_warehouses",
            "list_sql_warehouses",
            "list_warehouses_v2",
            "list_sql_warehouses_v2",
        ],
    )
    if not warehouse_tool:
        warehouse_tool = _find_tool_with_keyword(tools, "warehouse")
    if warehouse_tool:
        print(f"Test: {warehouse_tool}")
        _print_tool_result(client.call_tool(warehouse_tool, {}))
    else:
        print("Skipping warehouse listing (no warehouse tool advertised)")

    print("Test: list_catalogs")
    _print_tool_result(client.call_tool("list_catalogs", {}))

    print("Test: list_jobs")
    _print_tool_result(client.call_tool("list_jobs", {"limit": 10}))

    if warehouse_id:
        print("Test: execute_sql")
        _print_tool_result(
            client.call_tool(
                "execute_sql",
                {
                    "warehouse_id": warehouse_id,
                    "statement": "SELECT current_timestamp() as now, current_user() as user",
                },
            )
        )
    else:
        print("Skipping execute_sql (no warehouse ID provided)")


def run_conversation(client: MCPClient, warehouse_id: Optional[str]) -> None:
    client.initialize()

    prompts = [
        ("list_clusters", {}, "What compute clusters are running?"),
        ("list_schemas", {"catalog_name": "main"}, "What schemas exist in main?"),
        ("list_catalogs", {}, "What catalogs are available?"),
        ("list_jobs", {"limit": 10}, "What jobs are configured?"),
    ]

    for tool, args, label in prompts:
        print(f"Prompt: {label}")
        _print_tool_result(client.call_tool(tool, args))

    if warehouse_id:
        print("Prompt: run SQL query")
        _print_tool_result(
            client.call_tool(
                "execute_sql",
                {
                    "warehouse_id": warehouse_id,
                    "statement": "SELECT current_timestamp() as now, current_user() as user",
                },
            )
        )
    else:
        print("Skipping SQL prompt (no warehouse ID provided)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCP validation utility")
    parser.add_argument("--base-url", required=True, help="Base URL, e.g. https://<fqdn>")
    parser.add_argument("--warehouse-id", help="Warehouse ID for SQL tests")
    parser.add_argument(
        "--mode",
        choices=["init", "list-tools", "discover", "validate", "conversation"],
        default="init",
        help="Validation mode",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = MCPClient(args.base_url, timeout=args.timeout)

    try:
        if args.mode == "init":
            run_initialize(client)
        elif args.mode == "list-tools":
            run_list_tools(client)
        elif args.mode == "discover":
            run_discover(client)
        elif args.mode == "validate":
            run_validation(client, args.warehouse_id)
        elif args.mode == "conversation":
            run_conversation(client, args.warehouse_id)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
    except requests.exceptions.HTTPError as exc:
        print(f"HTTP error: {exc}")
        if exc.response is not None:
            print(exc.response.text[:800])
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
