"""Call the local Resolve Lua MCP server; guard Lua edits by native project ID."""
import argparse
import asyncio
import json
import os
from pathlib import Path

from mcp import StdioServerParameters
from praisonai_shorts_studio.live import mcp_client
from praisonai_shorts_studio.live.lua import lua_string

ROOT = Path(__file__).resolve().parents[1]


def _legacy_server():
    return StdioServerParameters(command=str(ROOT / "scripts/resolve-live-mcp"), cwd=str(ROOT), env=dict(os.environ))


async def call_tool(name, arguments=None):
    server = None if os.environ.get("RLB_MAC_CONSOLE") == "1" else _legacy_server()
    return await mcp_client.call_tool(name, arguments, server=server)


async def run_guarded(project_id: str, code: str):
    legacy = os.environ.get("RLB_MAC_CONSOLE") != "1"
    return await mcp_client.run_guarded(project_id, code, server=_legacy_server() if legacy else None, legacy=legacy)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool")
    parser.add_argument("arguments", nargs="?", default="{}")
    parser.add_argument("--lua-file", type=Path)
    parser.add_argument("--expected-project-id")
    args = parser.parse_args()
    if args.tool == "run_lua":
        if not args.lua_file or not args.expected_project_id:
            parser.error("run_lua requires --lua-file and --expected-project-id")
        data = await run_guarded(args.expected_project_id, args.lua_file.read_text())
    else:
        if args.lua_file or args.expected_project_id:
            parser.error("The Lua file and document guard apply to run_lua")
        data = await call_tool(args.tool, json.loads(args.arguments))
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
