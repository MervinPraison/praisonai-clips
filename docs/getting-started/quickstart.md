# Make your first clip

[Install the prerequisites](installation.md) and configure your API key first. Run commands from the repository root.

## See an example first

Open [the homepage example](../index.md#see-example) to watch a silent generated clip, or start the dashboard and choose **Download the example bundle**. The example needs no API key and makes no API calls. Its captions and edit are scripted; it demonstrates rendering and exported files, rather than AI selection or editorial acceptance.

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

Open [the local dashboard](http://127.0.0.1:8501). On your first visit, add a recording directly in the main screen. Open **Use a local file or adjust clip settings** for local paths, clip count, and duration. Uploads support up to 2 GB; use a path for larger files. **Create my clips** becomes available when a source is selected and processing prerequisites are ready.

After starting a job, select the recording and open **Source evidence**. Pick a source-time window to see the video, local audio waveform, word-level transcript, and screen descriptions together. The transcript and visual observations appear when their processing stages finish; select **Refresh source evidence** to reload them. This panel does not make additional AI requests. Playback does not automatically follow the chart. Word timings are estimates, the screen is sampled about every five seconds, and quiet audio may still contain speech, so listen and inspect before cutting.

## Review the output

```sh
.venv/bin/python scripts/serve_preview.py
```

Open [the preview gallery](http://127.0.0.1:8765/preview/index.html). Review framing and captions, and listen before publishing. Uncertain results remain in `drafts/`; accepted clips are in `accepted/`. The preview server exposes the local data directory on localhost.

[Understand processing and review →](../guides/workflow.md)
