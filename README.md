# PraisonAI Clips

Create reviewed vertical Shorts from a full-length video using the OpenAI Python SDK and FFmpeg. Local Streamlit upload screen, durable SQLite jobs, independent five-second vision analysis, dense crop inspection, word-highlight captions, automatic crop repair, and an HTML preview gallery.

## Setup

Requires Python 3.11+ and FFmpeg with libx264, libass and loudnorm (Debian/Ubuntu: `sudo apt install ffmpeg python3-venv`).

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env  # only on first setup; preserve your existing .env
```

Set `OPENAI_API_KEY` in `.env`. The default vision/editor model is `gpt-4o-mini`. Transcription uses `whisper-1` because measured word timestamps are required. OpenAI usage is billed to your API account; source audio and sampled frames are sent to OpenAI. No automatic publishing.

```bash
.venv/bin/praisonai-clips doctor
.venv/bin/streamlit run app.py
```

Open http://127.0.0.1:8501. The app binds to localhost. Uploads up to 2GB are enabled; choose an existing local path for larger videos.

## Process the main video

```bash
.venv/bin/praisonai-clips run 'input/main video.mp4'
```

Defaults: up to five non-overlapping, self-contained Shorts, 30–60 seconds each, 1080×1920 MP4. Fewer clips are returned when suitable moments or acceptance evidence are insufficient. The first pass normalizes the full source timeline, which takes CPU time before transcription starts.

```bash
.venv/bin/praisonai-clips list
.venv/bin/praisonai-clips status JOB_ID
.venv/bin/praisonai-clips cancel JOB_ID
.venv/bin/praisonai-clips resume JOB_ID
```

Cancellation interrupts FFmpeg promptly; in-flight API requests finish and cache their responses before stopping. Resume after the worker releases its lock. If the original source changed, create a fresh job.

## HTML preview

```bash
.venv/bin/python scripts/serve_preview.py
```

Open http://127.0.0.1:8765/preview/index.html. The local gallery refreshes while jobs run and does not interrupt playing videos. Streamlit also provides a ZIP download for each accepted Short. The preview server exposes the local data directory on localhost; run this as a private local tool.

## Artifacts

`data/jobs/<job-id>/accepted/clip-NN/` contains `video.mp4`, `captions.srt`, `captions.ass`, `words.json`, `edl.json` and `review.json`. Uncertain results stay in `drafts/`. `timeline.json` records the common source origin and `manifest.json` lists accepted and uncertain results. API responses and frame samples are cached per source/configuration/prompt version. Raw inputs and data are ignored by Git.

`words.json` preserves both measured source timestamps and output timestamps. EDL mappings remain explicit after each cut. No word timings or visible speaker identities are invented. Dense sampling chooses a stable crop only when the evidence supports it; full-frame fit preserves slides and screen recordings.

## Validation

```bash
.venv/bin/pytest -q
```

Tests cover real FFmpeg renders, offset source timestamps and delayed audio, nonadjacent-cut word mapping, caption clock rounding and escaping, sentence/duration guards, cancellation and cache reuse. See `M0_REPORT.md` for actual environment/API validation, `architecture.md` for design contracts, and `prd.md` for acceptance criteria.

Review uses full technical decode and timestamp checks plus sampled visual inspection. It cannot guarantee caption accuracy, catch every between-frame event or independently verify audible synchronization. Listen before publishing. The fetched OpenAI documentation schedules `whisper-1` shutdown on February 26, 2027; a verified alignment replacement will be needed before then.

## Optional editable Kdenlive export

With the separately installed pinned runtime from `docs/KDENLIVE_MCP_HANDOVER.md`:

```bash
.venv/bin/praisonai-clips export-kdenlive JOB_ID
```

The dashboard also has an optional export action. Each clip gets `kdenlive/editable.kdenlive`, measured caption sidecars, a rounded EDL and durable revisioned MCP state. Use `scripts/kdenlive-compatible` (Kdenlive 26.04). Keep the normalized source in place: projects reference it externally. This exports editable source cuts with portrait settings, not the finished FFmpeg layout/audio/caption effects, and does not control an open editor window. Existing timeline edits are never silently overwritten on resume.

For the separate experimental live editor and MCP adapter, see [docs/KDENLIVE_LIVE_CONTROL.md](docs/KDENLIVE_LIVE_CONTROL.md). Its actual build/test status is recorded there and under `data/kdenlive-live-test/`; registration of a tool is not proof that it has passed a live test.

On macOS, `scripts/kdenlive-mac-live` provides a separate experimental native Qt
bridge and seven MCP tools for live framing, seeking, sequence selection,
undo/redo, and saving. Real Mac MCP tests verified zoom changes and native
undo/redo against rendered frames, then restored the original framing. See the
[Mac setup and validation](docs/KDENLIVE_LIVE_CONTROL.md#native-mac-live-bridge).

Resolve on this Mac now has an opt-in AppleScript Lua Console MCP adapter.
Live tests on free Resolve 21.1.2 verified zoom, pan and crop changes, native
frame export, project guards and pixel-identical framing restoration.
The upstream file-mailbox and external Python connections remain unavailable. See [Resolve setup and current limitations](docs/RESOLVE_LIVE_CONTROL.md).

This is the independent PraisonAI Clips project. The existing praisonai-shorts repository is unchanged. The internal Python package retains the name praisonai_shorts_studio.

Live Kdenlive testing succeeded on a fresh native project: splits, linked audio/video, undo/redo, save and screenshots. This remains experimental; the demo uses a rendered clip with burned-in captions, and importing the other backend's project crashed this build. See [the live-control report](docs/KDENLIVE_LIVE_CONTROL.md) for the tested scope.

## Documentation site

The MkDocs site follows the [PraisonAI design kit](https://praison.ai/design-kit/).

```sh
.venv/bin/pip install -e '.[docs]'
.venv/bin/mkdocs serve --dev-addr 127.0.0.1:8001
.venv/bin/mkdocs build --strict
```

Open http://127.0.0.1:8001. The static build is written to `site/`; these commands do not publish it.

## Live Resolve SDK and reusable skill

```sh
.venv/bin/pip install -e '.[live]'
.venv/bin/praisonai-resolve status
.venv/bin/praisonai-resolve-mcp
```

Use `from praisonai_shorts_studio.live import ResolveClient, ClipTarget, Framing`.
The SDK shares guarded framing operations across Python, CLI and eight MCP tools.
Its Mac Console transport and licensed Lua helpers ship in the wheel, so the
working route needs no separate upstream checkout or npm build. See
[the SDK reference](docs/reference/resolve-sdk.md) and
[the reusable Resolve Mac skill](skills/resolve-mac-live/SKILL.md).
The skill's [maintained runbook](skills/resolve-mac-live/references/runbook.md)
records setup, failed approaches, AppleScript details and repeatable live checks.
