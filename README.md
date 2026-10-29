> **This project was built entirely using OpenAI Codex.** Developed through prompts, iteration, debugging, testing, and deployment under Mervin Praison’s direction.

# PraisonAI Clips

**Turn recordings into clips. Edit them in DaVinci Resolve by chatting with Codex.**

Turn a long recording into a collection of captioned vertical clips. PraisonAI Clips finds complete moments, adapts the framing, checks the output, and keeps the source mappings available for review. Start in the local dashboard and refine through optional Kdenlive and DaVinci Resolve integrations.

## Edit in Resolve by chatting with Codex

Open a project in DaVinci Resolve and ask Codex to inspect the timeline, adjust a crop, or prepare a cut that removes quiet pauses. The editor updates on screen while you remain in control. For example:

> “Find the quiet pauses in this clip and make a new timeline so I can review the cuts.”

Codex can use the packaged MCP tools, the Python SDK, or the CLI. The pause workflow analyzes audio locally, shows an edit plan, and builds a separate timeline with linked video and audio segments. You can review the result in Resolve before saving or sharing. On the tested Mac, a 20-second excerpt became six segments with 0.9 seconds of quiet pauses removed.

**Get started:** [Connect Codex to Resolve](docs/reference/resolve-sdk.md) · [CLI and YAML examples](docs/reference/cli.md#remove-quiet-pauses) · [Mac setup and troubleshooting](skills/resolve-mac-live/references/runbook.md)

This is an experimental integration, tested with DaVinci Resolve Free 21.1 on macOS. Resolve must be open, the Mac unlocked, and the required Accessibility permissions enabled. Pause removal currently supports an unretimed 30 fps source clip on a 30 fps timeline; listen to the result because quiet audio can contain speech.

[Made, changed & checked](https://clips.praison.ai/built-with-codex/) · [Watch an example](https://clips.praison.ai/#see-example) · [Quickstart](docs/getting-started/quickstart.md) · [Workflow](docs/guides/workflow.md) · [CLI reference](docs/reference/cli.md) · [Editor integrations](docs/editors/index.md)

## Use the same workflow from the terminal

```sh
praisonai-clips doctor --check
praisonai-clips example --output example.zip
praisonai-clips run input/video.mp4 --max-clips 3
praisonai-clips manifest JOB_ID
praisonai-clips bundle JOB_ID clip-01 --output clip-01.zip
praisonai-clips preview --serve
praisonai-clips resolve --help
praisonai-clips kdenlive --help
```

The CLI shares processing, artifact exports, and guarded editor operations with the app and SDK. [Full CLI reference](docs/reference/cli.md).

## See what you can make

The dashboard includes a playable example and downloadable video, caption, and edit files. Explore it without an API key or API calls. The example uses generated graphics and scripted timings rendered through the app's caption and video pipeline; it demonstrates the output format without using private footage.

[View the sample clip](https://clips.praison.ai/assets/demo/clip.mp4) · [Compare the generated source](https://clips.praison.ai/assets/demo/source.mp4)

## Built for recordings with more to give

A webinar, product walkthrough, interview, or lesson can contain several useful stories. Finding those moments, reframing them, captioning them, and checking the result are separate editing tasks. PraisonAI Clips brings that sequence into one repeatable workflow.

| Who it helps | What they can create |
| --- | --- |
| Creators and interview hosts | Standalone moments from longer conversations |
| Educators and technical presenters | Short explanations that preserve important slides and screen content |
| Content teams | Captioned clips with review evidence and a path into desktop editing |

## Automation with editorial control

**Find → Frame → Caption → Review → Refine**

The product combines automated production with an inspectable handoff: measured captions, explicit source mappings, review evidence, and experimental control inside familiar editors.

- **Context before cutting.** Selection combines the transcript with sampled visual analysis to choose complete thoughts.
- **A review gate before delivery.** Uncertain results stay in drafts. Supported framing repairs can be attempted before a clip is accepted.
- **A source trail for every edit.** Word timings and edit mappings stay available alongside the rendered video.
- **Room for a human finish.** Preview and download locally, export Kdenlive source cuts, or refine live framing through the experimental editor adapters.

## Working today

The implementation includes end-to-end video processing, a local dashboard, downloadable clip bundles, resumable jobs, and a Python SDK with MCP tools for Resolve framing. Real-video validation and native editor tests are documented with their limitations; live editor integrations remain experimental.

[See the product and validation overview](docs/product.md) · [Read the initial processing report](M0_REPORT.md) · [Explore the Resolve SDK](docs/reference/resolve-sdk.md)

## Features

- **Moment selection:** identify self-contained, non-overlapping clips from a longer recording.
- **Evidence-based framing:** inspect sampled frames, apply a stable crop when supported, and preserve slides or screen recordings with full-frame fit.
- **Word-highlight captions:** retain measured source timestamps and explicit mappings to the edited output.
- **Review and repair:** check rendered media, attempt supported framing repairs, and keep uncertain drafts separate from accepted clips.
- **Resumable processing:** store jobs in SQLite and reuse cached API responses and frame analysis.
- **Local previews:** review clips in Streamlit or an HTML gallery and download accepted results.
- **Optional editor control:** export editable Kdenlive source cuts or use experimental live framing through Python and MCP.

By default, a job produces up to five 30–60 second clips at 1080 × 1920. It may produce fewer when suitable moments or sufficient review evidence are unavailable.

## Requirements

- Python 3.11 or later.
- FFmpeg and ffprobe, with `libx264`, `subtitles`/libass, and `loudnorm` support.
- An OpenAI API key with access to the configured transcription and vision models.

The core workflow runs on CPU. Editor integrations have additional, platform-specific requirements documented in their setup guides.

## Quickstart

```sh
git clone https://github.com/MervinPraison/praisonai-clips.git
cd praisonai-clips
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

# First setup only; keep an existing .env file.
cp -n .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then check the environment and process a video:

```sh
praisonai-clips doctor
praisonai-clips run '/absolute/path/to/video.mp4'
```

Or start the dashboard:

```sh
streamlit run app.py
```

Open [the local dashboard](http://127.0.0.1:8501). Upload files up to 2 GB, or select a local path for larger videos. See [installation](docs/getting-started/installation.md) for dependency setup.

OpenAI processes source audio and sampled frames; API usage is billed to your account. Source files, job state, and rendered outputs remain in your local workspace. Review [data handling](docs/reference/public-release.md) before sharing a repository or diagnostic bundle.

## Manage jobs and preview results

```sh
praisonai-clips list
praisonai-clips status JOB_ID
praisonai-clips cancel JOB_ID
praisonai-clips resume JOB_ID

# Optional browser gallery
python scripts/serve_preview.py
```

Open [the preview gallery](http://127.0.0.1:8765/preview/index.html). Cancellation stops FFmpeg promptly; an in-flight API request finishes and caches its response before stopping. Resume once the worker releases its lock. A changed source requires a new job.

The dashboard and gallery bind to localhost. The gallery serves the local data directory, including review artifacts, so keep it private.

## Output files

Each accepted clip is stored under `data/jobs/<job-id>/accepted/clip-NN/`:

| File | Purpose |
| --- | --- |
| `video.mp4` | Rendered vertical video with burned-in captions and normalized audio |
| `captions.srt`, `captions.ass` | Caption sidecars |
| `words.json` | Measured word timings in source and output coordinates |
| `edl.json` | Explicit source-to-output edit mapping |
| `review.json` | Review evidence and acceptance result |

Uncertain clips remain in `drafts/`. Job-level `timeline.json` and `manifest.json` record the source origin and output inventory. See [files and configuration](docs/reference/configuration.md) for details.

Automated review combines technical decoding and timestamp checks with sampled visual inspection. Listen and inspect the final clips before publishing; sampling cannot catch every visual event or verify every spoken word.

## Editor integrations

| Integration | Supported workflow | Setup |
| --- | --- | --- |
| Kdenlive export | Editable source cuts, portrait project settings, and remapped caption sidecars | [Runtime and export guide](docs/KDENLIVE_MCP_HANDOVER.md) |
| Kdenlive live control · experimental | Native framing, seeking, sequence selection, undo/redo, and saving on the tested Mac bridge; a separate Linux adapter is also available | [Live-control guide](docs/KDENLIVE_LIVE_CONTROL.md) |
| DaVinci Resolve · experimental | Guarded live zoom, pan, crop, native frame export, and saving through the macOS Lua Console | [Resolve guide](docs/RESOLVE_LIVE_CONTROL.md) |

Kdenlive source-cut export requires a separately provisioned runtime and does not reproduce every FFmpeg layout, audio, or caption effect. Live editor changes do not automatically update the pipeline's EDL or review manifest. Consult each guide for the tested scope and version constraints.

### Resolve SDK and MCP

```sh
python -m pip install -e '.[live]'
praisonai-resolve status
praisonai-resolve-mcp
```

The Python SDK exposes `ResolveClient`, `ClipTarget`, and `Framing` from `praisonai_shorts_studio.live`. Shared validation and project identity guards support the Python API, CLI, and MCP tools. The macOS transport and licensed Lua helpers ship with the package.

Start with the [SDK reference](docs/reference/resolve-sdk.md), [reusable Resolve skill](skills/resolve-mac-live/SKILL.md), and [setup and recovery runbook](skills/resolve-mac-live/references/runbook.md).

## Development and documentation

```sh
python -m pip install -e '.[dev,docs]'
pytest -q
mkdocs build --strict
mkdocs serve --dev-addr 127.0.0.1:8001
```

Open [the local documentation site](http://127.0.0.1:8001). The MkDocs Material site follows the [PraisonAI design kit](https://praison.ai/design-kit/); the static build is written to `site/`.

Tests cover FFmpeg rendering, timing and caption mapping, candidate validation, cache reuse, cancellation, and editor adapter guards. Live editor tests are opt-in and require disposable projects. See [architecture](architecture.md), [acceptance criteria](prd.md), and the [initial validation report](M0_REPORT.md) for implementation context.

Before contributing, review the [public-release checklist](docs/reference/public-release.md). Keep source media, API responses, credentials, and editor runtime files out of commits. The distribution and primary CLI are named `praisonai-clips`; the internal Python package is `praisonai_shorts_studio`.
