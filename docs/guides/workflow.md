# Processing and review

## From source to clip

1. **Normalize.** Establish a common source timeline and a 30 fps working video.
2. **Transcribe.** Record measured word timestamps and retain the source time for every word.
3. **Inspect.** Analyze sampled frames at five-second intervals and inspect candidate crops more densely.
4. **Select.** Choose complete, non-overlapping moments within the requested duration range.
5. **Render.** Apply stable framing or full-frame fit, highlighted captions and audio normalization.
6. **Review.** Decode the result, check timestamps and inspect sampled visual evidence. Accepted results and uncertain drafts remain separate.

A screen recording or slide presentation can use full-frame fit to preserve content. A crop is used only when the evidence supports one. Selection and framing do not invent visible speaker identities.

## Choose where to stop

In the dashboard, choose **Analyze source only**, **Find moments for review**, or **Create review clips** before starting. The first stops after transcript and visual analysis; the second also selects source moments; the third completes rendering and review. At either review point, inspect the available evidence and continue later. Reused cached analysis does not repeat the same provider calls, though later stages can make additional billed calls.

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

Technical checks and sampled visual inspection cannot guarantee caption accuracy or catch every event between inspected frames. Listen to the complete clip and check text, framing and cut boundaries before sharing. Nothing publishes automatically.

For native adjustments, see [editor workflows](../editors/index.md). For output paths, see [files and configuration](../reference/configuration.md).
