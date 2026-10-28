"""macOS UI transport; no MCP dependency, repository paths, or runtime downloads."""
from importlib.resources import files
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import uuid

from ..errors import ResolveTransportError
from ..lua import lua_string, validate_envelope


class MacOSConsoleTransport:
    """Execute Lua through AppleScript, preserving clipboard and pending input.

    Requires Resolve running, an unlocked Mac, and Accessibility permission for
    the host app. Calls briefly focus the Lua Console. No mouse events are sent.
    """
    def __init__(self, state_dir: Path | None = None, timeout: float = 60):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.state_dir = Path(state_dir) if state_dir else Path.home() / "Library/Caches/praisonai-clips/resolve"
        self.timeout = timeout

    def execute(self, code: str) -> dict:
        if sys.platform != "darwin":
            raise ResolveTransportError("MacOSConsoleTransport requires macOS")
        import fcntl
        resources = files("praisonai_shorts_studio.live.resources")
        source = resources.joinpath("bridge.lua").read_text()
        script = resources.joinpath("console.applescript").read_text()
        marker = "RLB_RESULT_" + uuid.uuid4().hex
        # Split the marker so the Console's echoed command cannot count as a reply.
        command = ("local m=assert(loadstring(" + lua_string(source) + "))('RLB_BRIDGE_TESTING'); "
                   "local r=m.run_chunk({resolve=resolve,fusion=fusion}," + lua_string(code) + "); "
                   "print('RLB_RESULT_'..'" + marker.removeprefix("RLB_RESULT_") +
                   "'..m.hex(m.fit_response(r,r.result,64)))")
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with (self.state_dir / "console-control.lock").open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                response = subprocess.run(["/usr/bin/osascript", "-e", script, command, marker],
                                          text=True, capture_output=True, timeout=self.timeout)
        except BlockingIOError as error:
            raise ResolveTransportError("Another Resolve Console call is in progress; wait for it to finish") from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ResolveTransportError("Console call failed or timed out; inspect Resolve before retrying an edit") from error
        if response.returncode:
            raise ResolveTransportError(response.stderr.strip() + "; inspect Resolve before retrying an edit")
        matches = re.findall(re.escape(marker) + r"([0-9a-f]+)", response.stdout)
        if not matches:
            raise ResolveTransportError("No Lua Console reply; inspect Resolve before retrying an edit")
        try:
            envelope = json.loads(bytes.fromhex(matches[-1]))
        except (ValueError, UnicodeError) as error:
            raise ResolveTransportError("Invalid Console reply; inspect Resolve before retrying an edit") from error
        return validate_envelope(envelope)
