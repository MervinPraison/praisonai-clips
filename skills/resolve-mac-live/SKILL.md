---
name: resolve-mac-live
description: Set up, troubleshoot, test, and perform live DaVinci Resolve edits on macOS with the PraisonAI Clips SDK and MCP, including the tested Free-edition Lua Console route.
---

# Resolve Mac Live

Use the installed `praisonai_shorts_studio.live` SDK and its MCP server for live
Resolve operations. Read [the runbook](references/runbook.md) for setup, the
specific failures that led to the working route, and native validation steps.
The same runbook is included in the repository's MkDocs site; edit this source
rather than maintaining a second copy.

## Start with evidence

- Locate the project's Python environment or installed `praisonai-resolve` command.
  Install the local checkout with `python -m pip install -e '.[live]'` if needed.
- Run `praisonai-resolve status` with Resolve open and the Mac unlocked. This
  invokes AppleScript; a working check returns the actual open project's UUID.
- If macOS denies Accessibility, the user must enable the host app named by
  macOS. Reuse an existing grant; do not repeatedly ask them to launch scripts.
- The packaged Console route needs no npm, upstream clone, manual Lua menu-script
  launch, or Python bridge token. A Python SDK import, an MCP tools list, a menu
  click, and an old preference session are each insufficient proof of live control.

## Edit through the shared SDK

Use `ResolveClient` directly or MCP tools. Read `get_timeline_items` and preserve
its complete clip target. `set_framing` verifies project, timeline and clip UUIDs
inside the native invocation. Record `get_framing` before a change; apply both
zoom axes for uniform zoom. Restore the recorded values explicitly when testing.
For additional official API operations, use `run_lua` with the observed native
project UUID. An identity guard does not authorize unrelated destructive edits.

A Console call briefly takes focus and uses/restores the clipboard; it sends no
mouse events. Avoid competing keyboard input. If an edit times out or produces
no reply, inspect the current properties before deciding whether to repeat it:
the edit may already have executed. Do not blindly retry mutations or restart
Resolve on an unconnected server's "WEDGED" warning.

## Prove completion

For a disposable test timeline, run the repository's
`scripts/test_resolve_mac_live.py` with its explicit project UUID and timeline
name. It checks native readback, different before/after frame pixels, exact
restoration, and saves last. Keep test evidence under ignored `data/`.

For user edits, check the intended framing, save when requested, and leave the
review timeline visible. Do not claim native undo/redo, full editor automation,
or a different transport was tested based on this framing test.
