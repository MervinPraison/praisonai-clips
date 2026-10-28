"""Optional stdio MCP client. The default server is the installed SDK module."""
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .lua import guard_project


async def call_tool(name, arguments=None, *, server=None):
    parameters = server or StdioServerParameters(command=sys.executable, args=["-m", "praisonai_shorts_studio.live.mcp"],
                                                env=dict(os.environ))
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            if name == "list_tools":
                return {"tools": [t.model_dump(mode="json") for t in (await session.list_tools()).tools]}
            response = await session.call_tool(name, arguments or {})
            data = response.structuredContent
            if data is None:
                message = "\n".join(c.text for c in response.content if c.type == "text")
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {"text": message}
            is_error = response.isError
    if is_error:
        raise RuntimeError(json.dumps(data))
    return data


async def run_guarded(project_id: str, code: str, *, server=None, legacy=False):
    console = not legacy
    arguments = {"code": code, "expected_project_id": project_id} if console else {"code": guard_project(project_id, code)}
    response = await call_tool("run_lua", arguments, server=server)
    if not response.get("ok") or response.get("truncated"):
        raise RuntimeError(json.dumps(response))
    return response.get("result")
