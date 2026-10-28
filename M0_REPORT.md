# M0 / first end-to-end run — 28 October 2026

## Validation fixture and toolchain

- A local four-minute validation video was used. Original filenames, media checksums, and job identifiers are omitted from this public report; detailed evidence remains in ignored local artifacts.
- Source presentation duration: 240.000s video, 240.007s container; 1920×1080. The AAC tail must not be sampled as a nonexistent final video frame.
- Python 3.11.2; CPU processing, without a GPU requirement.
- FFmpeg/ffprobe 5.1.7; libx264, libass/subtitles and loudnorm available.
- OpenAI Python SDK 2.54.0. Actual paid calls to whisper-1 and gpt-4o-mini succeeded using environment-based credentials.

## Verified outcomes

Actual transcription returned 538 word measurements. Fourteen provider tokens had zero duration. Their original measurements remain in transcript.json with alignment warnings. Candidate selection excludes any range containing such tokens; timings were never invented. Punctuation is recovered from the same API transcript using matched lexical tokens without modifying timestamps.

Validation included actual gpt-4o-mini visual analysis at all 48 five-second samples, 0 through 235 seconds. Six API batches, frame artifacts, source SHA, independent observation method and original timestamp origin are saved under data/main-video-visual/. That evidence was imported into the job's matching cache, avoiding duplicate billed overview calls.

Selection now uses a deterministic pool of admissible sentence ranges before model ranking, preventing the model from inventing invalid cut indexes or ignoring duration limits. Thirteen valid ranges produced three nonoverlapping edits:

| Short | Source seconds | Render length | Result |
|---|---|---|---|
| Validation clip 1 | 80.600–115.390 | about 34.8s | Accepted |
| Validation clip 2 | 25.020–60.470 | about 35.5s | Uncertain draft |
| Validation clip 3 | 201.400–236.590 | about 35.2s | Uncertain draft |

Each selected range received half-second frame inspection. The full-width presentation material required fit/padding. All three were rendered to real 1080×1920 H.264/AAC MP4 files with audio normalization and burned-in word-highlight captions. Each has SRT, ASS, measured source/output word JSON, EDL and review artifacts. Full decode, output dimensions/codecs, A/V start times and expected duration passed on all three.

Initial sampled model review returned vague clipping claims even on full-frame fits. The review protocol was corrected to require concrete timestamps, original-source reference frames, explicit caption intervals, and a constrained repair enum. One Short passed every revised review batch at the acceptance threshold. Two remain quarantined with their actual review evidence; no acceptance threshold was bypassed. The picture at the first draft's reported 20.920001s was independently inspected and shows the complete caption, illustrating that model review can produce false positives. That draft remains separate because the automated reviewer did not fully accept it.

The localhost HTML gallery and Streamlit dashboard run successfully. Streamlit's app test reports no exceptions. The gallery can be opened directly in a local browser.

## Dependency / implementation defects found and fixed

- Installing the package required updating the virtual environment's setuptools and wheel.
- FFmpeg's loudnorm output needed an explicit stereo channel layout after resampling.
- Provider word arrays lacked transcript punctuation; matched text restores punctuation without touching measurements.
- Zero-duration provider word measurements are preserved and disqualify containing ranges rather than crashing the whole job or receiving fabricated durations.
- Audio container tails are excluded from overview frame sampling.
- Selection is constrained to validated ranges; model-authored raw word indexes were unreliable.
- Review distinguishes intentional letterboxing, source design, valid transitions and silent caption gaps from introduced defects.

## Optional Kdenlive export

Read and preserved docs/KDENLIVE_MCP_HANDOVER.md and tools/kdenlive-mcp-linux-x11.patch. The application uses the pinned standard Node MCP client bridge with stable client ID praisonai-shorts. Each actual Short was exported to an editable source-cut project with linked A/V, portrait project settings, exact revision checks, source hash checks and persisted MCP state. Seconds are rounded half-up once at 30fps, with the quantized mapping and errors recorded. Caption sidecars are remapped against that rounded EDL.

All three exported XML projects were parsed and checked for 1080×1920 profiles and matching half-open source cuts. Export uses external-reference normalized source media. The app does not claim Kdenlive GUI rendering parity, editable caption insertion, live GUI control, title fidelity, or MCP rendering parity. FFmpeg remains the delivery renderer. No render_submit job is used by the editable-export adapter; its persisted MCP job-ID list is empty by design. Broader MCP rendering/cancellation validation belongs to the handover's separate backup-video test.

## Regression validation

The suite includes real fit/crop renders and full decode, a nonzero source PTS plus delayed-audio normalization test, source/output mapping over nonadjacent cuts, caption escaping and clock rounding, sentence/duration safeguards, zero-duration exclusions, cache/cancellation behavior, a full synthetic end-to-end crop-repair/accept/resume test, HTML escaping, and optional Kdenlive frame-rounding boundaries. Synthetic transcripts appear only in clearly labeled test fixtures.

Result: **16 tests passed**. Kdenlive export was run twice for all three actual clips; each project stayed at revision 2 with no duplicate clips.

Run: `.venv/bin/pytest -q`. Automated review is sampled, not full auditory verification. Listen before publishing.
