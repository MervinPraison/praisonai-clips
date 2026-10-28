"""Thin MCP bindings for the public live SDK; importing the SDK needs no MCP."""
from pathlib import Path
from .models import ClipTarget
from .resolve import ResolveClient


def create_server(client: ResolveClient | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:
        raise RuntimeError("Install praisonai-clips[live] to serve MCP") from error
    client = client if client is not None else ResolveClient()
    server = FastMCP("resolve-mac-console")

    @server.tool()
    def resolve_status() -> dict:
        """Read the running Resolve version and current project identity."""
        return client.status()

    @server.tool()
    def get_project_info() -> dict:
        """Read the current project's identity and timeline count."""
        return client.project_info()

    @server.tool()
    def get_timeline_items(track_index: int = 1) -> list[dict]:
        """Read video clips, native identity targets and framing properties."""
        return client.timeline_items(track_index)

    @server.tool()
    def get_framing(target: ClipTarget) -> dict:
        """Read framing after checking the project, timeline and clip identity."""
        return client.get_framing(target).to_dict()

    @server.tool()
    def set_framing(target: ClipTarget, changes: dict[str, float]) -> dict:
        """Apply framing fields and return before/after values for restoration.

        Pass both zoom_x and zoom_y for uniform zoom. Native undo is unavailable;
        restore by passing the returned before fields to this tool.
        """
        return client.set_framing(target, **changes)

    @server.tool()
    def save_project(expected_project_id: str) -> dict:
        """Save only the project with this native UUID."""
        return {"saved": client.save_project(expected_project_id)}

    @server.tool()
    def export_frame(expected_project_id: str, path: str) -> dict:
        """Export the current frame to a new local PNG, without overwriting a file."""
        return {"path": str(client.export_frame(expected_project_id, Path(path)))}

    @server.tool()
    def run_lua(code: str, expected_project_id: str) -> dict:
        """Execute official Lua API operations guarded by the native project UUID.

        Record original properties before edits. Errors can follow partial changes;
        inspect the editor rather than blindly retrying. Restore properties explicitly.
        """
        return client.run_lua(code, expected_project_id=expected_project_id)

    return server


def main():
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
