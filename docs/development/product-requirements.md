# PraisonAI Shorts — product requirements

## Goal

Convert a full-length video into compelling, self-contained, vertical Shorts with synchronized captions, editable evidence and an easy local preview. Ship one working end-to-end path first; expand only after validating actual rendering.

## MVP user journey

1. Configure OPENAI_API_KEY in the ignored .env file.
2. Upload or choose a local video in Streamlit, or run the CLI. Default source for this project is input/main video.mp4.
3. Request up to five Shorts, normally 30–60 seconds. Explicitly shorter test clips are permitted by CLI.
4. Observe durable progress. Cancel and resume without losing completed paid analysis.
5. Preview accepted videos in an HTML gallery or Streamlit and download MP4, SRT, ASS, word-timed JSON and EDL.
6. Inspect uncertain drafts separately. Nothing is published automatically.

## Acceptance criteria

- Source is validated and has a documented, shared A/V timeline.
- Word timings originate from transcription measurements, never estimated from text length.
- A separate visual stage inspects every five seconds, including scenes, actions, screens, text, subject positions and confidence.
- Selection uses both transcript and visual evidence, preserves full sentences, retains meaning, respects duration limits and returns fewer than requested if quality is insufficient.
- Shortlisted clips receive denser inspection (0.5-second sampling) for crop decisions. Screen text and important actions are preserved; uncertain crops use full-frame fit.
- Every output includes a structured EDL and original-to-output word mappings.
- Accepted video is 1080×1920 H.264/AAC MP4 with burned-in, measured-time captions, normalized audio and downloadable caption formats.
- Full decode and technical timeline checks pass. Sampled visual review accepts with at least 0.85 confidence and no defects; crop repair is attempted once where appropriate.
- Failed or uncertain renders stay in drafts and never appear in the accepted gallery.
- SQLite plus filesystem caches survive interruption. Same-job concurrent workers are rejected. Changed source files cannot reuse stale analysis.
- UI communicates paid API use and the scope of automatic review. Keys never enter source control or preview output.

## Milestones

M0 — Validate prerequisites: Python/CPU/FFmpeg filters, installed SDK contracts, actual API word timestamps, actual gpt-4o-mini frame analysis, timeline tests with nonzero source PTS and delayed audio, caption mapping and a real local render.

M1 — One working Short: real source transcription → independent visual overview → selection → dense crop inspection → EDL → captions → render → review → playable preview. Evidence recorded in data/ and docs/reference/validation-report.md.

M2 — Up to five Shorts, conservative overlap rejection, durable jobs, cancellation, resume, cache, separate accepted/draft output and downloadable bundles.

M3 — Local upload/dashboard and portable HTML preview; setup documentation and regression tests.

## Out of scope

Automatic publishing, public hosting, multi-user authentication, billing portal, social account connection, Kdenlive integration, diarization-to-face matching, sophisticated motion tracking and voice cloning.

## Quality boundary

The MVP performs full technical decode/timestamp validation and sampled visual model review. It does not independently listen to rendered speech. Caption accuracy and editorial judgment remain bounded by provider output; preview and listen before publishing.
