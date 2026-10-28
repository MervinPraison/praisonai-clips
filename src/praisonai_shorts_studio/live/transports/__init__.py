"""Inject a Lua transport to extend the live editor SDK."""
from typing import Any, Protocol


class LuaTransport(Protocol):
    """Return an ok/result/prints envelope, or raise; do not retry mutations."""
    def execute(self, code: str) -> dict[str, Any]: ...


from .macos_console import MacOSConsoleTransport

__all__ = ["LuaTransport", "MacOSConsoleTransport"]
