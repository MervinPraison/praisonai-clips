"""Build, launch, query, or serve MCP for a native Mac Kdenlive editing session."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

from build import build
from client import LiveClient

ROOT = Path(__file__).resolve().parents[2]


def serve(connection: Path):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("Kdenlive Mac Live")
    client = lambda: LiveClient(connection)

    @mcp.tool()
    def get_live_status() -> dict:
        """Read the guarded running document, clip IDs, sequences, and undo history."""
        return client().status()

    @mcp.tool()
    def select_sequence(index: int) -> dict:
        """Activate a native sequence using its index from get_live_status."""
        return client().select_sequence(index)

    @mcp.tool()
    def seek(frame: int) -> dict:
        """Seek the active sequence to a frame (30 fps for the current test project)."""
        return client().seek(frame)

    @mcp.tool()
    def set_framing(clip_id: int, x: float, y: float, width: float, height: float) -> dict:
        """Edit the active clip's native Transform rectangle in project pixels.

        The clip must have exactly one Transform effect. In a 1080x1920 project,
        [0,0,1080,1920] is full-frame; [-135,-240,1350,2400] is centered 125%.
        Edits occur in the running editor and use native undo history.
        """
        return client().transform(clip_id, x, y, width, height)

    @mcp.tool()
    def undo() -> dict:
        """Undo one native Kdenlive editing command in the guarded document."""
        return client().undo()

    @mcp.tool()
    def redo() -> dict:
        """Redo one native Kdenlive editing command in the guarded document."""
        return client().redo()

    @mcp.tool()
    def save_project() -> dict:
        """Save the guarded live project through Kdenlive's native Save action."""
        return client().save()

    mcp.run()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=ROOT / "data/mac-live")
    parser.add_argument("--application", type=Path, default=Path("/Applications/kdenlive.app"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    launch = sub.add_parser("launch")
    launch.add_argument("project", type=Path, help="An existing native .kdenlive project copy")
    sub.add_parser("status")
    sub.add_parser("mcp")
    call = sub.add_parser("call")
    call.add_argument("operation", choices=["status", "select_sequence", "seek", "transform", "undo", "redo", "save"])
    call.add_argument("arguments", nargs="?", default="{}")
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    connection = runtime / "connection.json"
    if args.command == "build":
        if connection.exists():
            try:
                os.kill(json.loads(connection.read_text())["pid"], 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError("Close the isolated editor before rebuilding its bridge")
        app, library = build(runtime, args.application.resolve())
        print(json.dumps(dict(application=str(app), library=str(library))))
    elif args.command == "launch":
        project = args.project.resolve(strict=True)
        if project.suffix != ".kdenlive":
            raise ValueError("Expected a .kdenlive project copy")
        if connection.exists():
            try:
                os.kill(json.loads(connection.read_text())["pid"], 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError("A session is already running in this runtime directory")
        app = runtime / "Praison-Kdenlive-Live.app"
        library = runtime / "libpraison-live.dylib"
        if not app.exists() or not library.exists():
            raise RuntimeError("Run the build command first")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        token = secrets.token_hex(32)
        env = dict(os.environ, DYLD_INSERT_LIBRARIES=str(library), PRAISON_KDENLIVE_PORT=str(port), PRAISON_KDENLIVE_TOKEN=token)
        with (runtime / "editor.log").open("w") as log:
            process = subprocess.Popen([str(app / "Contents/MacOS/kdenlive"), "--no-welcome", str(project)],
                                       env=env, stdout=log, stderr=log, start_new_session=True)
        state = dict(pid=process.pid, port=port, token=token, project=str(project))
        fd = os.open(connection, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        client = LiveClient(connection)
        deadline = time.monotonic() + 60
        error = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Editor exited; inspect editor.log")
            try:
                ping = client.request(op="ping")
                if ping["pid"] != process.pid:
                    raise RuntimeError("Bridge PID does not match launched editor")
                client.bind()
                print(json.dumps(client.status(), indent=2))
                return
            except (OSError, RuntimeError, KeyError) as exc:
                error = exc
                time.sleep(0.5)
        raise RuntimeError(f"Editor not ready; session was left running. Inspect editor.log. Last error: {error}")
    elif args.command == "mcp":
        serve(connection)
    else:
        client = LiveClient(connection)
        operation = "status" if args.command == "status" else args.operation
        arguments = {} if args.command == "status" else json.loads(args.arguments)
        print(json.dumps(getattr(client, operation)(**arguments), indent=2))


if __name__ == "__main__":
    main()
