# Resolve on macOS: working setup and recovery

This is the maintained operational record for the PraisonAI Clips live Resolve
adapter. It is shared by the `resolve-mac-live` skill and the MkDocs site.
The observed environment on **2026-10-28** was Apple Silicon, macOS, and
**DaVinci Resolve Free 21.1.2.10**. Recheck capabilities on another version;
these observations are not promises about every Free or Studio build.

## The working route

```text
Python SDK or MCP tools
    → ResolveClient (shared operations and identity checks)
    → LuaTransport.execute(code)
    → MacOSConsoleTransport
    → osascript / System Events / Resolve's Lua Console
    → official native Resolve Lua API
    → capped JSON envelope, hex encoded with a unique response marker
```

The native application is unmodified. The transport uses AppleScript keyboard
and accessibility actions, without mouse movement. The Console is briefly
visible. The previous attempt to mirror Fusion preference replies is not part
of this route.

The package includes the unmodified MIT-licensed Lua helper source from
[saadk408/davinci-resolve-lua-mcp](https://github.com/saadk408/davinci-resolve-lua-mcp),
commit `a10acbc33b5fc3976832d575425c7b35ae1432af` (v0.2.0). Loading it with
`RLB_BRIDGE_TESTING` returns its serializer and bounded execution/capture helpers;
it does **not** start its mailbox loop. The original source, license and SHA256
provenance ship as SDK package resources. The working route needs no checkout
under `data/`, npm build, network listener, bridge token or menu-script bootstrap.

## First setup and reconnection

From the repository root:

```sh
python3 -m venv .venv                 # first setup only
.venv/bin/pip install -e '.[live]'
.venv/bin/praisonai-resolve status
```

If the environment lacks pip, use
`uv pip install --python .venv/bin/python -e '.[live]'`.
Open Resolve and a project before the status check. Leave the Mac unlocked.
The working SDK itself uses the standard library; the `live` extra supplies MCP.
FFmpeg is needed for the rendered-pixel comparison test, not for connection.

On `osascript is not allowed assistive access` (`-1728`), open **System Settings →
Privacy & Security → Accessibility** and have the user enable Codex, Terminal,
or the host app macOS identifies. This grant cannot be inferred from an SDK
import. Once enabled, retry the read-only status check. Preserve existing grants.

Select **Lua** in Workspace → Console if its language was changed. The adapter
can open the Console itself. The tested Console exposes live `resolve` and
`fusion` globals as userdata, not Python `scriptapp` connections.

Success means the result contains `alive: true`, the actual Resolve version,
and the open project's native UUID. A project can be absent; inspection methods
that need one then fail clearly. Importing the SDK does not connect to an app.

### MCP registration

Use the absolute entry-point path in the environment where the package was installed:

```sh
codex mcp add davinci-resolve-mac-console -- \
  /absolute/path/to/.venv/bin/praisonai-resolve-mcp
```

The server exposes `resolve_status`, `get_project_info`, `get_timeline_items`,
`get_framing`, `set_framing`, `export_frame`, `save_project`, and `run_lua`.
It delegates to the same SDK as direct Python calls. Registering the server is
not a live test; call `resolve_status` and inspect its actual response.

Existing compatibility paths still work:

```sh
RLB_MAC_CONSOLE=1 scripts/resolve-live-mcp
RLB_MAC_CONSOLE=1 .venv/bin/python scripts/call_resolve_live.py resolve_status
```

Without the flag, the old wrapper selects the separately installed upstream
Node mailbox server. That is a legacy, independently configured route and has
not passed a live handshake on the observed Mac. Prefer the installed SDK entry
point for the tested route.

## What made AppleScript reliable

| Observation | Working implementation |
| --- | --- |
| Process and application names differ | System Events targets process `Resolve`; the app is named DaVinci Resolve. |
| Console title is missing, not an empty string | Find the `AXFloatingWindow`, then its text areas; do not depend on its title. |
| Window ordering changes when raised | Re-evaluate the accessibility query for each action; cached `window 1` or `window 2` references targeted the wrong window. |
| Console opens asynchronously | Wait for the floating window after invoking Workspace → Console. |
| The app must receive input | Bring process `Resolve` to the front, raise the Console, then focus its input. |
| Direct AX text assignment did not reliably submit Qt input | Paste the complete command through the clipboard and submit Return. |
| Long `keystroke` strings were dropped or corrupted | Use Command-A and Command-V after checking pending input; preserve and restore the clipboard record on success and error. |
| Pending Console input could belong to the user | Refuse nonempty input; do not clear it automatically. |
| Console echoes the command itself | Construct the unique reply marker from separate Lua strings, so its complete value appears only in the actual output. |
| Opening another Resolve page hides the Console | Reopen it while waiting for the result; do not rerun the operation. |
| Multiple clients could interleave input/clipboard changes | Use one nonblocking file lock shared by SDK calls in the state directory. |

The default lock lives in
`~/Library/Caches/praisonai-clips/resolve/console-control.lock`. An explicit
`state_dir` can be supplied to the transport. Clients controlling the same app
must use the same directory to share the lock.

A timeout, missing reply, malformed envelope or truncated result has an uncertain
outcome. The transport does not retry. The result reader tolerates transient
window disappearance and reopens the Console without resending the command. Lua/native errors can also follow partial
changes. Inspect Resolve and read the current properties before a further edit.
Long-running or UI-blocking operations require care; this transport was validated
for short inspection, framing, frame-export and save operations.

## Attempts that did not establish a working connection

### External Python and the most popular MCP server

The installed official SDK and ARM64 Python imported successfully, but
`DaVinciResolveScript.scriptapp("Resolve")` returned `None`. The tested Free
installation did not list the installed Python bridge scripts in Workspace →
Scripts. Its presence on disk and a user menu click were not connection proof.

[samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp)
v4.16.0, commit `c347df6cb598edf74a3df40a17753389122fa102`, was the most popular
of six compared projects at the time (3,823 stars). Installation, import,
MCP initialization and enumeration of 37 tools succeeded. The live version
request returned `SCRIPTING_UNAVAILABLE`; the authenticated Python bridge
listener was not responding. This server remains separate from the working SDK
Console adapter. Popularity and successful tool enumeration did not establish
native scripting capability.

The server also emitted a misleading `WEDGED` database warning while the API
was unconnected. That was insufficient evidence to restart or repair Resolve.
Do not repeat installations, restarts or purchases based on that warning alone.

### Lua menu bridge and Fusion preference replies

Lua menu-script startup can be silent. Asking the user to look for a visible
change or a printed Console message was not a reliable startup check.
A session record eventually appeared in `Fusion.prefs` during Resolve shutdown;
its PID was stale after restart. A saved `state: running` session did not prove
that the current process was answering requests.

In the observed Lua **Console** environment:

- `resolve` and `fusion` were usable userdata.
- `loadstring` and `setfenv` were functions.
- `loadfile`, `io`, `python`, `bmd.runScript`, `bmd.writefile`, and
  `fusion.SavePrefs` were absent in the probes performed.
- `bmd.fileexists` and `bmd.wait` were present.

Calling `fusion:SavePrefs(...)` in the Console raised a missing-method error.
The earlier explicit filename trial produced no reply file and was reverted.
The upstream mailbox relies on `loadfile` and preference persistence, so the
Console adapter bypasses both. These probes describe the Console; do not assume
all script hosts or Resolve versions expose identical globals.

No modified Resolve binary, license workaround, Python bridge token, or repeated
manual script launch was needed to make the Console route work.

## Native API details learned during the live test

- Use current SDK references shipped under
  `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/`.
  Methods differ by version; do not assume a newer Python stub guarantees the
  same Lua calling convention.
- In the observed Lua host, `MediaPool:ImportMedia({{FilePath=path}})` returned
  no clip. `MediaPool:ImportMedia({path})` imported the same file successfully.
  Inspect the media pool before retrying an ambiguous import to avoid duplicates.
- The test used the latest selected source, normalized to its first four minutes,
  then selected roughly 30 seconds into a separate `PraisonAI Live Crop Review`
  timeline. Its portrait settings were 1080 × 1920 at 30 fps. Check actual frame
  boundaries and duration rather than assuming source in/out conventions.
- `TimelineItem:GetProperties()` and `SetProperties()` worked for `ZoomX`,
  `ZoomY`, `Pan`, `Tilt` and crop edges. Uniform zoom should set both axes.
  Zoom and crop are different properties; record the complete framing snapshot.
- A project UUID alone cannot identify the intended clip. The SDK additionally
  checks active timeline UUID, video-track index, clip index and clip UUID in
  the same native invocation, rejecting stale selections or reordered clips.
- Native timeline undo/redo is not exposed by this adapter. Restore captured
  properties explicitly; do not use application-wide keyboard undo as a substitute.
- `Project:ExportCurrentFrameAsStill(path)` produced native 1080 × 1920 PNGs.
  Identical file sizes did not mean identical images. Compare decoded RGB pixels,
  since image metadata and container hashes can vary.
- Save **after** frame exports and restoration. Exporting after saving left the
  project marked Edited in the observed UI.

## Repeatable live verification

Use an explicitly identified disposable timeline with exactly one video clip.
Do not clear or rebuild a user's timeline to make a test fit.

```sh
.venv/bin/praisonai-resolve status
.venv/bin/praisonai-resolve timeline
.venv/bin/python scripts/test_resolve_mac_live.py \
  --project-id PROJECT_UUID \
  --timeline-name 'PraisonAI Live Crop Review'
```

The test calls the installed SDK's real stdio MCP server. It records the original
framing, exports a frame, changes zoom/pan/crop, exports again, restores in a
`finally` block, compares all framing fields and decoded pixels, and saves last.
It writes a fresh evidence directory under ignored `data/resolve-live/`.
It seeks to `01:00:10:00` by default; choose `--timecode` within the test clip.
The seek/playhead is deliberately left at the test point.

The initial live test proved native changes from zoom 1 → 1.25, pan 0 → 40 and
left crop 0 → 20. Native exports changed, and restoration matched the original
pixel for pixel. The SDK refactor adds the repeatable test and identity guards;
see each run's report for that run's result.

After a completed call, close the Console through its accessibility close button
when needed and leave the review timeline visible. Save the project after the
last operation that marks it dirty. Keep source videos in place: native timelines
reference their source files externally. None of this testing publishes media.

## Legacy installation audit

These steps record the earlier experiments; they are unnecessary for the packaged
Console transport. `scripts/setup_resolve_live.py` cloned the pinned Lua project
under `data/resolve-live/lua-reference`, ran `npm ci --ignore-scripts`, built its
Node server, and ran its upstream tests. The archived results were 93 Node and
274 standalone Lua checks passing; they were not live editing tests.

It installed `resolve_mcp_bridge.lua` and its license under the user's
`~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/`.
The installer preserved different existing scripts, made its state directory
0700, stamped the request path and raised a diagnostic error when startup could
not acquire the objects. That diagnostic patch did not fix preference persistence.
Automatic upstream installation was disabled with `RLB_AUTO_INSTALL=0`.

The popular server checkout is under `data/resolve-live/popular-mcp`, with its own
Python environment. It was installed with `--clients manual --update-policy never`
and registered separately as `davinci-resolve-popular`, preserving other entries.
Its authenticated bridge config was private (0600) and bound to localhost; tokens
are not part of this runbook or the skill. The installed Python menu scripts did
not appear in the tested Resolve Scripts menu, and its listener remained closed.

Historical evidence remains in ignored `data/resolve-live/`, including installation
logs, `popular-validation.json`, `popular-mcp-test.json`, and the original
`console-{validation,crop-test,crop-restored,render-validation}.json`. The packaged
SDK has its own `sdk-live-test.json` and per-run `sdk-test-*/report.json` evidence.
Do not reuse old session PIDs or a previous project's UUID as current identity.

The SDK's isolated wheel was also exercised against the real open project without
MCP installed or checkout resources. A page-switch probe deliberately hid the
Console; recovery returned the original reply, and a native counter confirmed
that the operation ran exactly once (`sdk-console-recovery.json`).
