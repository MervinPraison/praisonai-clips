# Live Resolve SDK

The live editor integration is part of the installed `praisonai-clips` package.
The Python API uses the standard library; MCP is an optional adapter supplied by
`praisonai-clips[live]`. Importing the SDK does not launch or connect to Resolve.

For the tested Mac setup and all troubleshooting findings, read
[the shared skill runbook](../editors/resolve-runbook.md).

## Install and connect

```sh
.venv/bin/pip install -e '.[live]'
.venv/bin/praisonai-resolve status
.venv/bin/praisonai-resolve timeline
.venv/bin/praisonai-resolve-mcp
```

`praisonai-resolve-mcp` is a stdio MCP server; it waits for a client.
`praisonai-resolve mcp` is equivalent. The Console transport ships its Lua and
AppleScript resources in the wheel. It needs no repository-local `data/` files,
npm, upstream checkout or menu-script installer. macOS Accessibility permission,
an unlocked desktop and an open Resolve project are needed for live operations.

## Python API

```python
from praisonai_shorts_studio.live import ClipTarget, Framing, ResolveClient

resolve = ResolveClient()
status = resolve.status()
items = resolve.timeline_items(track_index=1)
# Choose the intended clip after inspecting names and identities.
target = ClipTarget(**items[0]["target"])
original = resolve.get_framing(target)

change = resolve.set_framing(
    target,
    zoom_x=1.25,
    zoom_y=1.25,
    pan=40,
    crop_left=20,
)
resolve.save_project(target.project_id)

# When restoration is intended:
resolve.restore_framing(target, original)
resolve.save_project(target.project_id)
```

`set_framing` accepts partial changes and returns `target`, `before` and `after`.
The values in those snapshots use the same field names as `Framing`:

| Field | Native property | Validation |
| --- | --- | --- |
| `zoom_x`, `zoom_y` | `ZoomX`, `ZoomY` | Finite, positive |
| `pan`, `tilt` | `Pan`, `Tilt` | Finite |
| `crop_left`, `crop_right` | `CropLeft`, `CropRight` | Finite, nonnegative |
| `crop_top`, `crop_bottom` | `CropTop`, `CropBottom` | Finite, nonnegative |

Pass both zoom axes for uniform scaling. Invalid and unknown fields fail before
contacting the desktop. Native Resolve can impose further constraints.

A `ClipTarget` contains project, timeline and clip UUIDs, plus video track and
clip indices. The native Lua invocation checks all of them before the setter.
A reordered clip or switched project/timeline fails instead of editing whatever
happens to occupy the previous position. Fetch a fresh target after structural
edits. The SDK does not create native undo/redo behavior.

## Prepare a quiet-pause review timeline

```python
plan = resolve.plan_silence(target, threshold_db=-25, min_silence=0.3, padding=0.08)
print(plan["removed_ranges"], plan["removed_seconds"])
if plan["removed_ranges"]:
    result = resolve.apply_silence_plan(plan, timeline_name="Quiet pauses review")
    print(result["review"])
```

`plan_silence` analyzes the clip locally with FFmpeg. `apply_silence_plan` verifies source identity, creates a new timeline, preserves clip framing and timeline resolution, and adds corresponding video and audio segments. It currently requires an unretimed 30 fps source and timeline. A quiet passage may include speech: inspect and listen to the review timeline. Errors can leave a partially created timeline; inspect Resolve before retrying. The original timeline is not edited.

Resolve may report the last source frame inclusively at the end of a media file. The planner keeps that native boundary for its identity check and uses the clip duration to preserve the final frame in its half-open edit ranges. The apply step checks the native video and audio segment durations after insertion. This was tested on Resolve Free 21.1.2 on macOS; review the result on other versions and sources.

Agents can call the `plan_silence` and `apply_silence_plan` MCP tools. The [CLI and YAML reference](cli.md#remove-quiet-pauses) exposes the same options and SDK behavior.

## Frame exports and official API extensions

```python
from pathlib import Path

resolve.export_frame(target.project_id, Path("data/review/new-frame.png"))
resolve.save_project(target.project_id)  # save after exports

result = resolve.run_lua(
    "return guarded_project:GetCurrentTimeline():GetName()",
    expected_project_id=target.project_id,
)
print(result["result"])
```

Frame export accepts a new `.png` path and refuses to overwrite an existing file.
The parent directory is created locally. It exports the current timeline frame;
seek or inspect that timeline first. The project guard does not select a clip or
imply permission for unrelated operations in an arbitrary Lua program.

`run_lua` returns the bounded `ok/result/prints` envelope. Its project UUID guard
runs in the same native invocation. There is a 64 KB response cap. A Lua error
may follow partial changes; the escape hatch is not a transaction.

The equivalent CLI accepts a file:

```sh
praisonai-resolve run-lua /absolute/path/to/operation.lua --project-id PROJECT_UUID
```

## Modular design and extension points

```text
live/
  resolve.py              ResolveClient: shared native operations and guards
  models.py               ClipTarget, Framing and one native property mapping
  lua.py                  Lua string/number encoding and response validation
  errors.py               Shared operation and transport failures
  transports/
    __init__.py           LuaTransport protocol
    macos_console.py      AppleScript transport and serialization lock
  resources/              Packaged AppleScript, pinned Lua, license, provenance
  mcp.py                  Thin MCP bindings to ResolveClient
  mcp_client.py           Optional reusable stdio MCP client
  cli.py                  Command line entry point using the same SDK
```

A new transport only implements:

```python
from typing import Any

class MyLuaTransport:
    def execute(self, code: str) -> dict[str, Any]:
        # Deliver Lua through the selected host and return its result envelope.
        raise NotImplementedError

resolve = ResolveClient(transport=MyLuaTransport())
```

The contract is an envelope such as
`{"ok": true, "result": {...}, "prints": []}`. Return the native result unchanged;
the client validates failures and truncation. A custom transport must preserve
ordering and prevent interleaving with other clients controlling the same host.
Raise `ResolveTransportError` when delivery or the outcome is uncertain.
No transport should automatically retry a possibly executed mutation.

New editor operations belong in `ResolveClient`, using the shared Lua encoder,
project guard and clip guard where applicable. Add a thin MCP binding only when
needed. This keeps SDK, CLI and MCP behavior consistent. Existing scripts remain
compatibility wrappers; add no new native operation implementations there.

The Mac transport accepts `state_dir` and `timeout` constructor arguments.
Use one state directory across clients of the same Resolve instance to share
its nonblocking lock. `timeout` bounds the host subprocess; the Console resource
also has a 30-second reply deadline and 10-second AppleEvent timeouts. A timeout
can leave a native operation running; inspect Resolve before retrying. Normal
and AppleScript-error exits restore the clipboard; an external process kill can
interrupt that cleanup. The transport is intended for short live interactions.

## Validation

```sh
.venv/bin/pytest -q tests/test_resolve_sdk.py
.venv/bin/python scripts/test_resolve_mac_live.py \
  --project-id PROJECT_UUID --timeline-name 'PraisonAI Live Crop Review'
```

The regression suite exercises generated Lua in Resolve's bundled standalone
interpreter when available, rejects stale and injected identities before setters,
round-trips Lua strings, checks input validation, and verifies no timeout retry.
It makes no GUI calls. Interpreter-dependent tests skip where that interpreter
is absent.

The opt-in live test requires an explicitly identified disposable timeline with
one video clip. It uses the real stdio MCP server and records native framing and
decoded RGB frame comparisons. Original framing is restored in `finally` and the
project is saved last. Read its generated report for the actual result.
