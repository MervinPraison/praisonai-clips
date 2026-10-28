# Make your first clip

[Install the prerequisites](installation.md) and configure your API key first. Run commands from the repository root.

## Process a recording

```sh
.venv/bin/praisonai-clips doctor
.venv/bin/praisonai-clips run 'input/main video.mp4'
```

The default target is up to five non-overlapping clips, 30–60 seconds each, rendered as 1080 × 1920 MP4. A job can return fewer clips when suitable moments or review evidence are insufficient. Normalizing the source takes CPU time before transcription starts.

For a short initial test, prepare the first four minutes of a local source:

```sh
ffmpeg -i '/absolute/path/to/video.mp4' -t 240 \
  -c:v libx264 -c:a aac 'input/first-four-minutes.mp4'
.venv/bin/praisonai-clips run 'input/first-four-minutes.mp4' --max-clips 1
```

Use a new output filename if that file already exists.

## Use the dashboard

```sh
.venv/bin/streamlit run app.py
```

Open [the local dashboard](http://127.0.0.1:8501). Upload a video or choose a local path. Uploads support up to 2 GB; use a path for larger files.

## Review the output

```sh
.venv/bin/python scripts/serve_preview.py
```

Open [the preview gallery](http://127.0.0.1:8765/preview/index.html). Review framing and captions, and listen before publishing. Uncertain results remain in `drafts/`; accepted clips are in `accepted/`. The preview server exposes the local data directory on localhost.

[Understand processing and review →](../guides/workflow.md)
