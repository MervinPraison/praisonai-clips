"""Local SDK command line; use the mcp subcommand to expose the same operations."""
import argparse
import json
from pathlib import Path
from .resolve import ResolveClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "project", "timeline", "mcp"):
        commands.add_parser(command)
    lua = commands.add_parser("run-lua")
    lua.add_argument("file", type=Path)
    lua.add_argument("--project-id", required=True)
    args = parser.parse_args()
    if args.command == "mcp":
        from .mcp import main as serve
        serve()
        return
    client = ResolveClient()
    if args.command == "run-lua":
        result = client.run_lua(args.file.read_text(), expected_project_id=args.project_id)
    else:
        result = {"status": client.status, "project": client.project_info, "timeline": client.timeline_items}[args.command]()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
