# Edit in your native editor

| Workflow | What it does | Validation |
| --- | --- | --- |
| Kdenlive export | Writes editable source cuts, portrait project settings and caption sidecars | Separate pinned runtime required |
| Kdenlive live on macOS | Controls framing, seeking, selection, undo/redo and saving in an open editor | Native MCP framing and rendered-frame checks passed on the test Mac |
| DaVinci Resolve | Installs Lua MCP and the popular Python MCP alternative | Mac Console MCP verified crop, pan, zoom and pixel-identical restoration; broader editing remains experimental |

## Kdenlive

```sh
praisonai-clips export-kdenlive JOB_ID
```

An exported project references the normalized source. It contains editable cuts and sidecars; FFmpeg's finished layout, audio treatment and caption effects are not reproduced automatically. Export does not control an already open editor. Existing edits are preserved on resume.

Read [runtime installation](../KDENLIVE_MCP_HANDOVER.md) or [live control and Mac validation](../KDENLIVE_LIVE_CONTROL.md).

## DaVinci Resolve

The installed free edition has different scripting capabilities from Studio. A registered MCP server or a successfully launched menu script does not establish a working live connection. Read [Resolve setup and actual test results](../RESOLVE_LIVE_CONTROL.md) before attempting timeline changes.
