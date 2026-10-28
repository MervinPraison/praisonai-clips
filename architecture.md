# PraisonAI Shorts — MVP architecture

## Scope and decisions

Python 3.11, direct OpenAI Python SDK, FFmpeg/ffprobe, SQLite, filesystem artifacts, local Streamlit UI and portable HTML preview. PraisonAI, WhisperX, GPU acceleration and Kdenlive are not MVP dependencies. These documents were recreated from the user's requirements because the original planning documents were not present.

The first real source is `input/main video.mp4` (240 seconds). The other input videos are separate sources and must never be silently substituted.

## Pipeline

1. Probe source streams; fingerprint the entire file. Reject unreadable/incomplete files and missing audio/video.
2. Establish one canonical presentation timeline with FFmpeg. FFmpeg subtracts the common input format origin; 30fps normalization preserves relative stream offsets, fills initial gaps, and records source format start time. Never independently reset audio and video to their respective first samples.
3. Transcribe 600-second audio cores with one-second edge overlap using OpenAI `whisper-1`, verbose JSON and measured word/segment timestamps. Mono 16kHz PCM remains below the 25MB upload limit. Assign words to chunks by measured midpoint. Reject missing, invalid, or substantially overlapping measurements rather than fabricate timing. Failures remain resumable.
4. Independent vision agent: sample frames every five seconds in batches of eight, describing scenes, actions, screen content, visible text, normalized subject positions and confidence. No transcript or speaker identity is supplied. A separate development-time agent produced an actual main-video overview; its matching source SHA is checked before import into the durable job cache.
5. Editorial agent: combine transcript and visuals in bounded 180-second windows with 60-second overlap. Request global inclusive word indexes for self-contained moments, enforce complete sentence boundaries, duration limits and confidence. Deduplicate overlapping results and return up to five.
6. Inspect each shortlisted range every 0.5 seconds. Request conservative static framing in batches of twelve. Use crop only with high confidence and consistent crop centers across all batches; otherwise fit the full source with padding. This is dense sampling, not continuous subject tracking.
7. Store a structured edit decision list (EDL), remap measured words onto the output timeline, export SRT/ASS/word JSON, then render H.264/AAC at 1080×1920 and 30fps. FFmpeg loudnorm targets -16 LUFS, -1.5dBTP, LRA11 (single-pass dynamic normalization). ASS highlights each word only during its measured interval.
8. Review full decode, dimensions, codecs, output duration and A/V stream start alignment. Model review examines rendered frames every two seconds plus caption samples. A rejected crop can be repaired once with full-frame fit. Reject other defects or uncertain results; promote accepted artifacts atomically into accepted/.
9. Update a manifest and expose playable results through Streamlit or `scripts/serve_preview.py`.

## Timestamp contracts

All times are floating-point seconds on the canonical source presentation timeline. Approximate original container PTS is `canonical time + original format.start_time`. Video resampling has a 1/30-second quantization bound; source content remains at the common A/V origin. Review `timeline.json` to interpret original stream metadata and offset.

EDL mapping: `{source_start, source_end, output_start}`; `output_end = output_start + source_end - source_start`. Mappings must cover a contiguous output timeline starting at zero. Caption mapping: `output_word_time = output_start + measured_source_word_time - source_start`. Source word times are retained in `words.json`. Never stretch timings to fit captions.

The EDL schema and caption mapper support multiple ranges; the MVP renderer intentionally supports one continuous range per Short to preserve meaning and simplify verified rendering. Dense framing chooses a stable crop or fit, without inferred face/voice association.

## Storage and lifecycle

`data/jobs.sqlite3`: job ID, source path and SHA256, immutable JSON configuration, status, current stage, cancellation flag, error and timestamps.

`data/jobs/<id>/`: source.mp4, timeline.json, transcript.json, scenes.json, selection.json, manifest.json, cache/, frames/, drafts/, accepted/.

`accepted/clip-NN/` and `drafts/clip-NN/`: video.mp4, edl.json, words.json, captions.srt, captions.ass, review.json and review-attempt-N.json.

JSON writes use temporary files plus atomic replace. SQLite uses WAL. Nonblocking OS file locks prevent simultaneous workers on the same job. Cache keys include complete source SHA, job configuration, prompt version, stage and evidence. Completed paid calls are saved even if cancellation arrives during the request. FFmpeg polls cancellation; OpenAI calls are bounded by SDK timeout/retries and finish before observing cancellation. Interrupted stages are recomputed while completed API analysis is retained. Resume rejects changed source bytes. No automated publishing.

## API contracts and verification

Verified against OpenAI's official speech-to-text, vision, GPT-4o mini and structured-output documentation, and installed SDK 2.54.0. `gpt-4o-mini` accepts images and structured Responses output, but does not transcribe audio. `whisper-1` provides the required word timestamps. The fetched documentation marks whisper-1 deprecated, with shutdown on February 26, 2027; replace with a verified measured alignment provider before that date. Do not switch to a text-only transcript and distribute timings artificially.

Sources: https://developers.openai.com/api/docs/guides/speech-to-text ; https://developers.openai.com/api/docs/guides/images-vision ; https://developers.openai.com/api/docs/models/gpt-4o-mini ; https://developers.openai.com/api/docs/guides/structured-outputs

## Known MVP limits

Local single-user application, not an authenticated public service. Full source normalization adds latency but simplifies one verified timeline. Sampling can miss events between inspected frames. Model judgments and word alignment can be wrong. Technical A/V checks do not constitute auditory verification; listen before publishing. No speaker recognition, continuous tracking, editorial jump-cut assembly, explicit per-request budget cap, or silent fallback model. API pricing/limits depend on the configured account. Uploaded audio and sampled frames are sent to OpenAI. Files remain local until manually removed.

## Optional Kdenlive source-cut export

`kdenlive.py` and `scripts/kdenlive_export.mjs` bridge to the pinned local MCP SDK, using client ID praisonai-shorts. This is an optional editable source-cut path; it does not replace FFmpeg delivery. Every mutation uses an exact expectedRevision. Durable state records source/EDL hashes, project and asset IDs, clip IDs, revision, operations and exported artifact. Existing timelines are compared against the requested cuts before reuse; mismatches fail rather than overwrite. No render jobs are submitted by this adapter, so the persisted job-ID list remains empty.

Convert boundaries to half-open 30fps frames once using decimal half-up rounding, and retain rounding errors plus original mappings. Remap measured caption sidecars against the quantized EDL. Exported projects keep external source references. Caption insertion and FFmpeg visual/audio effect parity are explicitly excluded. Use the Kdenlive 26.04 compatible launcher; preserve the Linux X11 patch and broader validation boundaries in docs/KDENLIVE_MCP_HANDOVER.md.

Production review now compares sampled renders with original-source references, includes explicit caption-group intervals, and requires exact visible evidence for defects. Provider zero-duration words are retained with alignment warnings and excluded from admissible moments. Model ranking chooses from deterministically validated moment options instead of authoring raw cut indexes.
