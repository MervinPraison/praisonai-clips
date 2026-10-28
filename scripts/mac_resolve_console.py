"""Compatibility entry point for the packaged Resolve Console MCP adapter."""
from praisonai_shorts_studio.live.mcp import main
from praisonai_shorts_studio.live.transports import MacOSConsoleTransport


def execute(code):
    return MacOSConsoleTransport().execute(code)


if __name__ == "__main__":
    main()
