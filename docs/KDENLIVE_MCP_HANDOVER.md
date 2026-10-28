# Kdenlive MCP integration handover

Prepared 28 October 2026 for PraisonAI Shorts in `/absolute/path/to/praisonai-clips`.

## Decision and honest capability boundary

Basic editing through MCP is confirmed on the actual backup video: import, linked video/audio placement, two non-contiguous source cuts, revisioned edits, checkpoint creation, undo/redo, preview, H.264/AAC export, cancellation, and editable Kdenlive export. The exported project was opened in Kdenlive 26.04.2 and its two video/audio clips were visually inspected.

This is a **headless editing MCP**, not a remote control API for the currently open Kdenlive window. MCP edits its own canonical JSON/SQLite project. `interchange_export` creates a `.kdenlive` project; launching the desktop editor is a separate OS command. Desktop edits are not automatically reflected back into MCP. Do not promise live GUI synchronization.

Do not claim every feature is validated. The inventory below lists every discovered tool and separates real-video calls from features advertised in source but not exercised in the real-video test. Passing upstream tests is separate evidence, not end-to-end proof for every tool.

## Installed software and exact paths

| Item | Installation |
|---|---|
| MCP source | `tools/kdenlive-mcp` |
| Repository | https://github.com/AMMIROSOH/Kdenlive-mcp |
| Pinned commit | `b1ff6d5d0263c9074230b9a5d02a6a5d58d2386e` (detached HEAD) |
| MCP version | 1.1.0, 42 tools |
| Private Node | `tools/runtime/node/bin/node`, version 22.23.4 |
| Private pnpm | `tools/runtime/pnpm/node_modules/.bin/pnpm`, version 9.5.0 |
| MCP launcher | `/absolute/path/to/praisonai-clips/scripts/kdenlive-mcp` |
| Allowed root | `/absolute/path/to/praisonai-clips` only |
| Stable client ID | `codex` (use a distinct stable ID for the app) |
| Durable MCP state | `.kdenlive-mcp/` |
| Desktop Kdenlive | Private KDE AppImage 26.04.2, extracted under `tools/runtime/kdenlive-26.04.2/squashfs-root` |
| Desktop launcher | `/absolute/path/to/praisonai-clips/scripts/kdenlive-compatible` |
| Applications menu | **Kdenlive 26.04 (MCP compatible)** |
| System runtimes used by MCP | `/usr/bin/melt` 7.12.0, `/usr/bin/ffmpeg` and `/usr/bin/ffprobe` 5.1.7 |

The old `/usr/bin/kdenlive` is 22.12.3 and cannot load this server's project exports. Use the compatible launcher. The private AppImage SHA-256 was verified against KDE: `37548767032e2fd9bcb97002d588e119d1af5ea88dc12cec39409865522c45a5`.

The doctor passed all 14 checks. This machine's distribution MLT/FFmpeg are older than the repository's Linux CI versions; only the actual tests described here establish local behavior.

FFmpeg MCP and WhisperX were **not installed** during this work: the user redirected priority to Kdenlive MCP. The existing application retains its OpenAI transcription and FFmpeg implementation.

## What was actually tested

1. Connected a standard MCP SDK client over stdio to the launcher and discovered all 42 tools.
2. Created a 1920x1080, 30 fps project and imported `input/backup video.mp4` by external reference. The complete 4:20 source remains available in the project bin.
3. Added source frames `[0,150)` and `[300,450)` with linked A/V: source 0–5 seconds followed by source 10–15 seconds, giving a 10-second edit.
4. Created a checkpoint; added a text overlay, undid it, redid it, and removed it because visual testing found a text problem. Text is deliberately absent from the delivered cut test.
5. Validated the project and queried the resulting timeline. The delivered project has no title-safe warnings.
6. Generated and visually reviewed an MCP frame preview, rendered with `youtube-1080p`, and called `job_verify`.
7. Fully decoded the rendered video and audio with FFmpeg; inspected output frames at 1 and 6 seconds to check both source ranges. Video: H.264, 1920x1080, 30 fps, 300 frames, 10.000 seconds. Audio: AAC, stereo, 48 kHz, approximately 10.005 seconds. Container: approximately 10.006 seconds.
8. Submitted another export and cancelled it; confirmed terminal `cancelled` status. This confirms immediate submitted-job cancellation, not every possible mid-encode interruption/race.
9. Exported `.kdenlive`, launched Kdenlive 26.04.2 separately, and inspected the actual GUI: source present, two video clips, two audio clips, working picture/audio meters.
10. Compared the source SHA-256 with the hash captured at MCP import. Original backup was preserved: `<source-checksum>`.
11. Ran the pinned repository test suite after the local patch: **74 passed, 3 skipped; 15 test files passed, 1 skipped**. A targeted render-core run passed 22 tests with 1 skipped. These are upstream tests, not 74 independent real-video acceptance cases.

`job_verify` emitted one freeze warning on the delivered test. The source includes static presentation slides. Treat this as advisory and inspect the actual frames; do not automatically promote or reject based only on this warning.

## Known defects and local fix

### Rendering needs an X11 connection on this runtime

The first render returned success and passed `job_verify`, but its image was an MLT **INVALID** placeholder. Logs showed that the Qt MLT services could not initialize because the runtime dropped `DISPLAY`/`XAUTHORITY`. A decodable file is insufficient evidence of valid picture content.

Local patch: `tools/kdenlive-mcp-linux-x11.patch`. It adds only `DISPLAY` and `XAUTHORITY` to the subprocess environment allow list and includes a regression test. The launcher supplies the local defaults (`:0` and `$HOME/.Xauthority`) when the MCP host omits them. This is a desktop-specific setup; provision a proper X display or Xvfb for a headless service. The patch is applied in the checkout and built; preserve/reapply it when updating or reinstalling.

### Titles are not production-ready here

`text_edit` structurally succeeds, but qtext rendered the overlay much too large on system MLT. The pinned Kdenlive exporter also omits visible text overlays from the exported timeline, despite retaining canonical project metadata and reporting no fidelity warning. Final delivered artifacts have no added title. Do not enable title export/rendering as validated until both issues are fixed and visually tested.

### Other limitations

- There is no speech transcription, WhisperX alignment, visual scene understanding, automatic face tracking, or automatic highlight selection in this Kdenlive MCP. Local AI analysis is explicitly planned/unavailable upstream. Keep these tasks in the application.
- Crop/transform controls are not proof of moving face tracking or screen-preserving layout. These need separate implementation and visual acceptance tests.
- Kdenlive/OTIO export does not prove every effect/keyframe/caption survives GUI round-trip. Audit fidelity on the features the app uses.
- The discovered JSON schema for `interchange_import_plan` is empty in this SDK/server combination. Read its actual union schema in `apps/mcp-server/src/server.ts` before integrating imports; do not assume discovery describes that tool completely.
- Do not treat cached previews or metadata verification alone as sufficient QA. Inspect rendered frames, decode the whole output, verify expected source content and caption synchronization.

## Complete feature inventory

**Real call** means this tool completed against the backup-video test project. It does not mean every parameter variant is validated. **Unverified here** means exposed/documented in the pinned server, with no claim of real-video acceptance. Text has its own qualification.

| Tool | Feature | Validation |
|---|---|---|
| `project_create` | Create and open a canonical project inside an allowed root. | Real call |
| `project_open` | Open a project store inside an allowed root. | Unverified here |
| `project_get` | Read the open canonical project and current revision. | Unverified here |
| `project_validate` | Run deterministic full-project validation. | Real call |
| `project_checkpoint` | Create or replace a named checkpoint. | Real call |
| `project_checkpoint_restore` | Restore a named checkpoint as a new revision. | Unverified here |
| `project_undo` | Undo this client's latest eligible mutation. | Real call |
| `project_redo` | Redo this client's latest eligible mutation. | Real call |
| `media_import` | Import allowed-root media using managed-copy or external-reference mode. | External-reference mode passed; managed-copy unverified here |
| `media_list` | List assets in an open project. | Unverified here |
| `media_inspect` | Read one imported asset and normalized probe metadata. | Unverified here |
| `timeline_query` | Read a bounded, filtered, stably ordered timeline summary. | Real call |
| `timeline_add_track` | Add a video or audio track. | Unverified here |
| `timeline_add_clips` | Add, append, insert, or overwrite a batch of clips. | Real call |
| `timeline_move_clips` | Move clips with linkage and collision rules. | Unverified here |
| `timeline_remove_clips` | Remove clips as one mutation. | Unverified here |
| `timeline_split_clip` | Split a clip and optionally linked clips. | Unverified here |
| `timeline_trim_clip` | Trim a clip source range. | Unverified here |
| `timeline_slip_clip` | Slip source media without moving the clip. | Unverified here |
| `timeline_set_speed` | Set rational clip speed. | Unverified here |
| `timeline_ripple_delete` | Ripple-delete normalized frame ranges. | Unverified here |
| `clip_set_properties` | Set batched transform, crop, opacity, and audio properties. | Unverified here |
| `clip_set_keyframes` | Replace batched property keyframes. | Unverified here |
| `clip_set_effects` | Replace an ordered clip effect stack. | Unverified here |
| `transition_edit` | Add, update, or remove one transition. | Unverified here |
| `text_edit` | Add, update, or remove text entities as one mutation. | Structural call passed; visual/export defects above |
| `caption_edit` | Add, update, or remove timed captions as one mutation. | Unverified here |
| `caption_generate` | Convert timestamped transcript words into editable captions. The default YouTube layout repeats the prior line above each new line. | Unverified here |
| `marker_edit` | Add, update, or remove marker entities as one mutation. | Unverified here |
| `caption_export` | Export deterministic SRT or WebVTT captions into project artifacts. | Unverified here |
| `interchange_export` | Export the current canonical project as an editable Kdenlive 26.04.x project or OTIO 0.18.1 timeline. | Kdenlive real call + GUI opened; OTIO unverified here |
| `interchange_import_plan` | Parse a Kdenlive or OTIO file and create a client-owned reviewed import plan. It does not mutate any project. | Unverified here |
| `interchange_import_apply` | Atomically apply a reviewed interchange plan. Round-trip plans require the original expected revision. | Unverified here |
| `interchange_import_discard` | Discard a client-owned reviewed interchange plan without applying it. | Unverified here |
| `timeline_diagnostics_submit` | Submit a durable advisory timeline diagnostic job. It never mutates the project or blocks export. | Unverified here |
| `render_submit` | Submit a nonblocking export job using a validated built-in profile. | 1080p H.264/AAC passed; other profiles unverified here |
| `preview_submit` | Submit a nonblocking frame, range, or audio preview job. | Frame preview passed; range/audio preview unverified here |
| `preview_inspect` | Create a cached waveform or contact sheet. | Unverified here |
| `job_get` | Read an owned render/preview job and artifact resource URI. | Real call |
| `job_list` | List jobs owned by this client. | Unverified here |
| `job_cancel` | Cancel an owned queued or running job. | Real call |
| `job_verify` | Verify a successful owned export and return structured diagnostics. | Real call |

The eight built-in profiles exposed in source are `youtube-1080p`, `youtube-1440p`, `youtube-4k`, `shorts-1080x1920`, `mezzanine-ffv1`, `audio-wav`, `captions-srt`, and `captions-vtt`. Caption profiles use caption serializers, not `render_submit` media exports. The real test used only `youtube-1080p`.

Additional resources expose instructions, capability probes, export profiles, recipes, project summaries, preview/render artifacts, interchange artifacts/import plans, and timeline diagnostics. Stdio and authenticated loopback HTTP are implemented; only stdio was tested here. The JSON/SQLite stores provide revision checks, per-client undo and durable render jobs. Successful outputs are preserved; reviewed cleanup code removes abandoned temporary attempts and bounds failure diagnostics, not completed delivery artifacts.

## How to reproduce

Run from the project root:

```sh
scripts/kdenlive-mcp --doctor
# Creates a new independent test project on every invocation.
tools/runtime/node/bin/node scripts/test_kdenlive_mcp.mjs
scripts/kdenlive-compatible output/kdenlive-mcp-test/backup-mcp-test.kdenlive
```

The test script contains actual standard MCP `Client`, `StdioClientTransport`, `listTools`, and `callTool` calls. It does not simulate edits with direct FFmpeg commands. FFmpeg was used separately only for final decoding and frame inspection.

The launcher is registered as `mcp_servers.kdenlive` in `~/.codex/config.toml`, with 30-second startup and 3600-second tool timeouts. The original config was backed up as `config.toml.before-kdenlive-mcp`. Registered config and direct SDK stdio connectivity were checked separately; a running Codex session may need MCP reload/new chat to discover newly registered tools.

## Application integration guidance

The existing app is Python/Streamlit. `src/praisonai_shorts/pipeline.py` already drives evidence gathering and rendering; `models.py` has second-based EDL mappings; `media.py` currently renders via direct FFmpeg and intentionally accepts one mapping per Short. Add an optional editing/export adapter instead of replacing the functioning default path before parity is proven.

1. Launch the pinned MCP executable through a standard MCP client. Python can use the MCP Python SDK in an isolated optional dependency; alternatively use the working Node SDK example as a local bridge. Reserve stdout for MCP protocol; log to stderr. Give the application a distinct stable `--client-id praisonai-shorts` and do not mix its ownership with Codex jobs. The launcher allows additional arguments, so that final CLI client ID overrides its default.
2. Use explicit absolute roots under `/absolute/path/to/praisonai-clips`. Keep job-local canonical MCP project folders and persist project ID, current revision, source hash, asset IDs, clip IDs and MCP job IDs in the app's durable job records. Add the chosen client's SDK dependency explicitly; it is not installed into the app's Python environment by this handover.
3. Import the app's normalized `source.mp4` as external media (or use managed mode after testing). The source must remain accessible for external-reference projects.
4. Convert **seconds to integer project frames once**, consistently, at the boundary. At 30 fps, frame = round(seconds * 30). Source ranges are **half-open** `[sourceIn, sourceOut)`; 150 frames is 5 seconds. Preserve the app's source-to-output mappings after rounding. Keep linked A/V together.
5. Every mutation sends exact `expectedRevision`. Refresh on revision conflict rather than retrying stale edits. Successful edit calls typically return `{project, revision, changedIds, warnings, undoToken}`; `project_create` returns the project directly. Some successful calls, such as checkpoint creation, have no data payload. All tools use `{ok, data}` / `{ok:false, error}` envelopes; inspect MCP `isError` too.
6. Translate EDL mappings into `timeline_add_clips` append requests. Example after project creation/import:

```json
{
  "projectId": "<project UUID>",
  "expectedRevision": 1,
  "requests": [
    {"assetId":"<asset UUID>","sourceIn":0,"sourceOut":150,"linkedAv":true},
    {"assetId":"<asset UUID>","sourceIn":300,"sourceOut":450,"linkedAv":true}
  ],
  "options":{"mode":"append"}
}
```

7. For rendering, call `render_submit`, persist the returned job ID, poll `job_get`, mirror progress, and route app cancellation to `job_cancel`. Only terminal `succeeded` permits QA; cancelled/failed jobs must never be promoted. Preserve outputs on resume and preserve current app worker locks/caching.
8. Use `interchange_export(format="kdenlive")` for an optional editable-project download/open action. Launch `scripts/kdenlive-compatible` with an argument array and the exported absolute path. Label it **Open editable project in Kdenlive**; do not describe it as live control.
9. Keep the current reliable FFmpeg caption burn-in until MCP caption generation/export/burn-in and multiple-cut synchronization are tested. Keep existing measured transcription and independent five-second vision analysis. WhisperX is a separate future dependency, not supplied by this server.
10. Add focused integration tests: real two-cut frame/audio continuity, source-to-output caption mapping, vertical dimensions and screen-preserving layout, supported crop/transform, cancellation/resume, missing source handling, revision conflicts, and Kdenlive export fidelity. Do not claim all 42 tool families are ready from the smoke test alone.

## Evidence and deliverables

- Final editable project: `output/kdenlive-mcp-test/backup-mcp-test.kdenlive`
- Final 10-second video: `output/kdenlive-mcp-test/backup-mcp-test.mp4`
- Copied real-test report: `output/kdenlive-mcp-test/validation-report.json`
- Latest original report / complete call arguments and responses: `data/kdenlive-mcp-test/report.json`
- Complete discovered JSON schemas: `data/kdenlive-mcp-test/tools.json`
- Doctor: `tools/kdenlive-mcp-doctor.json`
- Upstream tests: `data/kdenlive-mcp-test/upstream-tests.log`
- Actual GUI screenshot after compatible open: `data/kdenlive-mcp-test/kdenlive26-window.png`
- Final rendered frames: `output/kdenlive-mcp-test/frame-1s.png`, `frame-6s.png`
- Reproducible standard MCP client: `scripts/test_kdenlive_mcp.mjs`
- Local source patch: `tools/kdenlive-mcp-linux-x11.patch`

Installation/build artifacts, model/media outputs, and server state are ignored in `.gitignore`; preserve the pinned source SHA and local patch for reproducible provisioning. This workspace was not a Git repository when checked. Application implementation files were not modified by this installation/test task.
