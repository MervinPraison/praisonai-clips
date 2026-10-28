"""Install a pinned Lua MCP bridge for the free Mac edition of Resolve 21.1.

The script must be started once per Resolve session from Workspace > Scripts.
This installer does not restart Resolve or alter an open project.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/resolve-live"
SOURCE = OUT / "lua-reference"
REPOSITORY = "https://github.com/saadk408/davinci-resolve-lua-mcp.git"
COMMIT = "a10acbc33b5fc3976832d575425c7b35ae1432af"


def patched_bridge(source: str, state: Path) -> str:
    source = source.replace("@@RLB_STATE_DIR@@", str(state))
    old = "  local st = start()\n  if st then run_loop(st) end"
    new = ('  local st, err = start()\n'
           '  if not st then error("Resolve MCP startup failed: " .. tostring(err)) end\n'
           '  run_loop(st)')
    if source.count(old) != 1:
        raise RuntimeError("Pinned bridge startup code changed; review before installing")
    return source.replace(old, new)


def main():
    if sys.platform != "darwin":
        raise RuntimeError("This setup targets the installed Mac Resolve edition")
    OUT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        subprocess.run(["git", "clone", "--no-checkout", REPOSITORY, str(SOURCE)], check=True)
        subprocess.run(["git", "-C", str(SOURCE), "checkout", "--detach", COMMIT], check=True)
    head = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    if head != COMMIT:
        raise RuntimeError("Preserving an existing checkout at a different revision")
    subprocess.run(["git", "-C", str(SOURCE), "diff", "--exit-code"], check=True, stdout=subprocess.DEVNULL)
    for label, command in (("npm-install", ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]),
                           ("build", ["npm", "run", "build"]), ("upstream-tests", ["npm", "test"])):
        with (OUT / (label + ".log")).open("w") as log:
            subprocess.run(command, cwd=SOURCE, check=True, stdout=log, stderr=log)
    state = OUT / "state"
    state.mkdir(mode=0o700, exist_ok=True)
    state.chmod(0o700)
    utility = Path.home() / "Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility"
    if not utility.is_dir():
        raise RuntimeError("Launch Resolve once to create its user Scripts directory")
    target = utility / "resolve_mcp_bridge.lua"
    upstream = (SOURCE / "bridge/resolve_mcp_bridge.lua").read_text()
    source = patched_bridge(upstream, state)
    previous = upstream.replace("@@RLB_STATE_DIR@@", str(state))
    explicit_save_trial = source.replace('return F:SavePrefs()',
        'return F:SavePrefs([==[' + str(state / "prefs/Default/Fusion.prefs") + ']==])')
    if target.exists() and target.read_text() not in (source, previous, explicit_save_trial):
        raise RuntimeError(f"Preserving a different existing bridge at {target}")
    target.write_text(source)
    target.with_suffix(".LICENSE.txt").write_text((SOURCE / "LICENSE").read_text())
    report = dict(source_repository=REPOSITORY, source_commit=COMMIT, script=str(target), state_dir=str(state),
                  script_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  next_step="In Resolve, open a project and run Workspace > Scripts > resolve_mcp_bridge")
    (OUT / "install.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
