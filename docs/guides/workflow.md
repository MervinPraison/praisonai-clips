# Processing and review

## From source to clip

1. **Normalize.** Establish a common source timeline and a 30 fps working video.
2. **Transcribe.** Record measured word timestamps and retain the source time for every word.
3. **Inspect.** Analyze sampled frames at five-second intervals and inspect candidate crops more densely.
4. **Select.** Choose complete, non-overlapping moments within the requested duration range.
5. **Render.** In the latest source checkout (not yet the PyPI release), detect quiet pauses within each selected moment, retain a safety margin around measured words, and join the remaining ranges. Apply stable framing or full-frame fit, highlighted captions and audio normalisation. Source mappings and caption timings follow the cuts.
6. **Review.** Decode the result, check timestamps and inspect sampled visual evidence. Accepted results and uncertain drafts remain separate.

A horizontal recording is still rendered as a 9:16 Short. The app samples frames across the selected moment and uses one stable crop only when it can keep the important picture content visible. Otherwise it fits the whole horizontal frame inside the vertical canvas with padding. This is useful for slides and screen recordings, where a tight crop could hide text. Selection and framing do not invent visible speaker identities.

## Choose where to stop

In the dashboard, choose **Analyze source only**, **Find moments for review**, or **Create review clips** before starting. The first stops after transcript and visual analysis; the second also selects source moments; the third completes rendering and review. At either review point, inspect the available evidence and continue later.

The latest source checkout caches the transcript and five-second screen descriptions locally. Resuming a job reuses its completed calls. A new job for the same unchanged recording also reuses those two analyses when it uses the same data directory, model and analysis version, even if you change the number or length of requested clips. Changing the recording or analysis model starts fresh calls. Selection, dense crop checks and final review can make additional billed calls. The cache stays on your computer under the chosen data directory; delete `analysis-cache/` there to discard it. The released PyPI package does not yet include this cross-job cache.

For the same choices at the command line:

```sh
praisonai-clips run /path/to/video.mp4 --until evidence
praisonai-clips resume JOB_ID --until selection
praisonai-clips resume JOB_ID --until render
```

The default `run` completes the render and review stages in one invocation. You can also describe a stage in YAML and run `praisonai-clips workflow workflow.yaml`:

```yaml
action: run
video: /path/to/video.mp4
until: selection # evidence, selection, or render
max_clips: 5
min_duration: 30
max_duration: 60
```

To continue an existing job, use `action: resume`, `job_id: JOB_ID`, and `until: render`. Relative video paths in YAML are resolved from the YAML file's directory. Python callers can use `Pipeline(store, job_id).run(until="selection")` and resume with `until="render"`.

## Continue in an editor

Download a reviewed clip bundle, unzip it, and import `video.mp4` into DaVinci Resolve or Kdenlive. This MP4 has the selected framing and captions baked in; the bundle includes separate caption files and source-time edit mappings. Draft bundles are available separately and need extra review. After import, configure the [Codex editor integration](../getting-started/codex.md) to request supported live adjustments. Importing and connecting the editor are separate steps; the pipeline does not automatically open or modify an editor.

For an editable Kdenlive **source-cut** timeline, the optional [Kdenlive export](../KDENLIVE_MCP_HANDOVER.md) provides external source references and caption sidecars; it does not recreate the rendered crop, captions or audio normalization. A comparable editable Resolve timeline export is not currently provided.

## Pause and resume

```sh
praisonai-clips status JOB_ID
praisonai-clips cancel JOB_ID
praisonai-clips resume JOB_ID
```

Cancellation interrupts FFmpeg promptly. An in-flight API request finishes and caches its response before stopping. Wait for the worker to release its lock before resuming. A changed original source requires a fresh job.

## Human review

Technical checks and sampled visual inspection cannot guarantee caption accuracy or catch every event between inspected frames. If the transcription provider gives a word zero duration, the app marks its short replacement timing as estimated in `transcript.json` and `words.json`; check those captions carefully. Quiet audio can still contain speech, and a pause cut can affect visual timing. Listen to the complete clip and check text, framing and cut boundaries before sharing. Nothing publishes automatically.

For native adjustments, see [editor workflows](../editors/index.md). For output paths, see [files and configuration](../reference/configuration.md).
