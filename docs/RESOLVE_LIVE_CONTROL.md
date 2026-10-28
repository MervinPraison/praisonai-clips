# Resolve live control on macOS

The tested route is the packaged **Mac Console SDK/MCP adapter** on DaVinci
Resolve Free 21.1.2.10. It controls the official native Lua API through AppleScript,
with no mouse movement. Calls briefly bring the Lua Console forward.

```sh
.venv/bin/pip install -e '.[live]'
.venv/bin/praisonai-resolve status
.venv/bin/praisonai-resolve-mcp
```

The working route ships its AppleScript, Lua helpers, license and provenance in
the Python wheel. It needs no upstream clone, npm build, manual menu-script
launch or bridge token. Resolve must be open, the Mac unlocked, and the host app
must have macOS Accessibility permission.

- [Setup, recovery, failed approaches and native API findings](editors/resolve-runbook.md)
- [Python SDK, MCP tools and transport extension points](reference/resolve-sdk.md)

The runbook is maintained once in the `resolve-mac-live` skill and included in
this site through a MkDocs build hook. The skill is installed in the test Mac's
Codex skills directory and can be invoked as `$resolve-mac-live`.

## Actual validation

The original native test verified project identity, zoom/pan/crop readback,
changed native frame pixels, and pixel-identical restoration. The SDK refactor
passed a real test through its installed stdio MCP server, including typed clip
targets, framing edits, native exports, explicit restoration and final save.

The regression suite also exercises generated Lua without touching a GUI,
rejects stale project/timeline/clip identities and injection attempts, validates
framing input, and checks that ambiguous timeouts never retry an edit.
An isolated wheel test confirmed imports and packaged resources work without
MCP installed or repository-local runtime files.

Re-run the live check only against an explicitly identified disposable timeline:

```sh
.venv/bin/python scripts/test_resolve_mac_live.py \
  --project-id PROJECT_UUID --timeline-name 'PraisonAI Live Crop Review'
```

Each run writes a new report and before/changed/restored PNGs under ignored
`data/resolve-live/sdk-test-*/`. The existing review timeline references the
normalized first four minutes of the latest selected source video. Keep that
source in place. Original framing is restored after tests; native undo/redo is
not provided. Broader rendering, delivery and structural editing have not been
exhaustively validated.

The original Lua mailbox and the separately installed popular Python MCP server
remain independent legacy routes. Neither completed a live connection on this
Mac. Their installation results and the reasons they did not work are preserved
in the shared runbook; a successful server install or tool list is not proof
of native control.
