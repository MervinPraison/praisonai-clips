"""Lua encoding and guards shared by SDK, MCP and compatibility clients."""
import math
from .errors import ResolveError, ResolveTransportError


def lua_string(value: str) -> str:
    def escape(char):
        if char in ('"', "\\"):
            return "\\" + char
        if ord(char) < 32 or ord(char) == 127:
            return "\\" + str(ord(char)).zfill(3)
        return char
    return '"' + "".join(escape(char) for char in value) + '"'


def lua_number(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Expected a finite number")
    return repr(value)


def guard_project(project_id: str, code: str) -> str:
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("A native project UUID is required")
    return ("local guarded_project=resolve:GetProjectManager():GetCurrentProject(); "
            "assert(guarded_project and guarded_project:GetUniqueId()==" + lua_string(project_id) +
            ", 'Refusing to edit a different Resolve project');\n" + code)


def validate_envelope(envelope: dict) -> dict:
    if not isinstance(envelope, dict) or type(envelope.get("ok")) is not bool:
        raise ResolveTransportError("Invalid Lua response; inspect Resolve before retrying an edit")
    if envelope.get("truncated"):
        raise ResolveTransportError("Lua result exceeded 64 KB; inspect Resolve before retrying an edit")
    if not envelope["ok"]:
        raise ResolveError(str(envelope.get("error", "Lua operation failed")))
    return envelope
