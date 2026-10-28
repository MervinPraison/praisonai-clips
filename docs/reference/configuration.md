# Files and configuration

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Required for processing | OpenAI API authentication |
| `SHORTS_VISION_MODEL` | `gpt-4o-mini` | Sampled visual analysis |
| `SHORTS_EDITOR_MODEL` | `gpt-4o-mini` | Clip selection and editorial reasoning |
| `SHORTS_TRANSCRIPTION_MODEL` | `whisper-1` | Transcription with measured word timestamps |
| `SHORTS_DATA_DIR` | `./data` | Local job storage |

Keep credentials in your environment or local `.env`; never add them to documentation or Git. Model replacements must preserve the workflow's required timestamp and structured-output capabilities.

## Job artifacts

Each job is stored under `data/jobs/JOB_ID/`.

| Path | Contents |
| --- | --- |
| `source.mp4` | Normalized working source |
| `timeline.json` | Common source origin and timeline mapping |
| `transcript.json` | Measured transcription |
| `scenes.json`, `selection.json` | Analysis and selected moments |
| `manifest.json` | Accepted and uncertain outputs |
| `cache/`, `frames/` | Cached responses and sampled frames |
| `drafts/` | Uncertain renders |
| `accepted/clip-NN/` | Accepted clip package |

An accepted package contains `video.mp4`, `captions.srt`, `captions.ass`, `words.json`, `edl.json` and `review.json`. Word data preserves both source and output timestamps. Keep the normalized source in place when an editor project references it.

Raw media, generated artifacts, installed editor runtimes and local credentials are ignored by Git.
