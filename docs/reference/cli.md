# Command line reference

Every processing and review workflow in the local app has a terminal route. The CLI calls the same pipeline, export helpers, and editor SDK operations; it does not require Streamlit. The global `--data-dir` option goes **before** the command. Paid analysis uses `OPENAI_API_KEY` from the environment or local `.env`.

```sh
praisonai-clips --data-dir ./data doctor --check
```

| Task | Command | Result |
| --- | --- | --- |
| Check setup | `doctor [--check]` | JSON diagnostics, readiness and missing prerequisites; `--check` exits 1 when setup is incomplete |
| Explore without an API key | `example --output example.zip` | Generated MP4, captions, word timings and edit mapping, included in the installed package |
| Process a recording | `run VIDEO` | Run the full transcription, selection, render, review and repair pipeline; paid OpenAI calls |
| List recordings | `list` | Durable jobs as JSON |
| Inspect progress | `status JOB_ID` | Job state as JSON |
| Cancel | `cancel JOB_ID` | Request worker cancellation; completed analysis remains cached |
| Resume | `resume JOB_ID` | Continue using cached analysis; refuses an active worker |
| Inspect results | `manifest JOB_ID` | Accepted clips, uncertain drafts and review evidence as JSON |
| Read a sidecar | `artifact JOB_ID clip-01 review.json` | Named artifact content on stdout |
| Download equivalent | `bundle JOB_ID clip-01 --output clip.zip` | The same explicit MP4/caption/mapping/review ZIP contents as the app |
| View results | `preview [--serve]` | Generate local HTML; optionally serve this workspace at `127.0.0.1:8787` until Ctrl-C |
| Export source cuts | `export-kdenlive JOB_ID` | Editable projects through the optional Kdenlive runtime |
| Live Resolve operations | `resolve --help` | All public Resolve SDK operations, including framing and restoration |
| Live Mac Kdenlive operations | `kdenlive --help` | Guarded status, sequences, seek, framing, undo, redo and save |

Commands return exit code 0 on success and 1 on operational errors; invalid arguments use argparse's exit code 2. JSON data goes to stdout; errors and the processing job ID go to stderr. `artifact` prints the requested file verbatim. `resolve mcp` reserves stdout for the MCP protocol. File exports refuse to overwrite existing destinations.

## Process, inspect and export

```sh
praisonai-clips run input/video.mp4 \
  --max-clips 3 --min-duration 30 --max-duration 60
praisonai-clips list
praisonai-clips status JOB_ID
praisonai-clips manifest JOB_ID
praisonai-clips artifact JOB_ID clip-01 review.json
praisonai-clips artifact JOB_ID clip-01 edl.json
praisonai-clips artifact JOB_ID clip-01 captions.srt
praisonai-clips bundle JOB_ID clip-01 --output clip-01.zip
praisonai-clips preview --serve --port 8787
```

Replace `JOB_ID` with the returned ID. Defaults are up to five clips, minimum 30 seconds and maximum 60 seconds; review may accept fewer. A missing prerequisite prevents processing before a job is created. Use `--draft` on `artifact` or `bundle` to explicitly select an uncertain draft. Exporting a draft does not mark it accepted. Supported artifacts are `review.json`, `edl.json`, `words.json`, `captions.srt` and `captions.ass`.

The preview server exposes the selected local data workspace to local processes on this computer. It serves read-only files and does not process recordings. It does not publish the workspace to GitHub Pages.

## Live Resolve: inspect, crop, restore

Both `praisonai-clips resolve` and the existing `praisonai-resolve` entry point expose the same subcommands. The optional MCP server uses the same SDK. First complete the [macOS Resolve setup](../editors/resolve-runbook.md), open a project and timeline, and allow the required macOS automation permissions. CLI access cannot bypass operating-system permissions.

```sh
praisonai-clips resolve status
praisonai-clips resolve project
praisonai-clips resolve timeline --track-index 1 --output timeline.json
```

Copy the `target` object for the intended clip from `timeline.json` into `target.json`. Include all five fields: `project_id`, `timeline_id`, `clip_id`, `track_index`, `clip_index`. These come from the running editor; do not invent UUIDs or rely on an index alone.

```sh
praisonai-clips resolve get-framing --target target.json
praisonai-clips resolve set-framing --target target.json \
  --zoom-x 1.15 --zoom-y 1.15 --pan 20 --tilt 0 --output framing-change.json
praisonai-clips resolve restore-framing \
  --target target.json --snapshot framing-change.json
praisonai-clips resolve export-frame frame.png --project-id PROJECT_UUID
praisonai-clips resolve save --project-id PROJECT_UUID
praisonai-clips resolve run-lua operation.lua --project-id PROJECT_UUID
praisonai-clips resolve mcp
```

Framing flags also include `--crop-left`, `--crop-right`, `--crop-top` and `--crop-bottom`. Zoom axes are independent: supply both for uniform scaling. A saved framing result contains `target`, `before` and `after`, and can itself be passed as `--target`. Restoration refuses a snapshot for another clip. `--output` writes JSON to a new file and checks the destination before a live mutation. Native errors can follow partial changes; inspect the editor after an error, rather than retrying blindly. Restore before values explicitly; Resolve native undo is not provided by this integration.

`run-lua` is the project-guarded escape hatch for other official Resolve API operations, including media import and timeline construction. Its Lua file has the same access as the SDK/MCP operation; use a project copy when exploring edits.

## Live Kdenlive on macOS

The packaged CLI can control an existing native bridge session. Building and launching the version-specific bridge still requires the repository, a compatible installed Kdenlive, and the [native setup instructions](../KDENLIVE_LIVE_CONTROL.md):

```sh
scripts/kdenlive-mac-live build
scripts/kdenlive-mac-live launch /absolute/path/to/project-copy.kdenlive
praisonai-clips kdenlive --connection data/mac-live/connection.json status
praisonai-clips kdenlive --connection data/mac-live/connection.json timelines
praisonai-clips kdenlive --connection data/mac-live/connection.json select-sequence 0
praisonai-clips kdenlive --connection data/mac-live/connection.json seek 30
praisonai-clips kdenlive --connection data/mac-live/connection.json set-framing CLIP_ID \
  --x -135 --y -240 --width 1350 --height 2400
praisonai-clips kdenlive --connection data/mac-live/connection.json undo
praisonai-clips kdenlive --connection data/mac-live/connection.json redo
praisonai-clips kdenlive --connection data/mac-live/connection.json save
```

Use the native `CLIP_ID` from `status`, rather than the pipeline's `clip-01` label. The clip must have exactly one native Transform effect. The private connection file contains authentication material; keep it local. Native document guards remain enabled. Linux's experimental DBus/MCP adapter retains its separate script interface, described in the editor guide.

## Development and publishing tools

Repository maintenance also has script entry points. These require a source checkout and their documented dependencies:

```sh
python scripts/build_demo.py
python scripts/build_walkthrough.py /path/to/browser-recording.webm
pytest -q
mkdocs build --strict
```

Git pushes trigger documentation deployment and portable CI. GitHub repository settings and DNS are deployment administration, outside the media-processing CLI. See each subcommand's `--help` for exact installed options.
