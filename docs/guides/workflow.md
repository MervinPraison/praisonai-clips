# Processing and review

## From source to clip

1. **Normalize.** Establish a common source timeline and a 30 fps working video.
2. **Transcribe.** Record measured word timestamps and retain the source time for every word.
3. **Inspect.** Analyze sampled frames at five-second intervals and inspect candidate crops more densely.
4. **Select.** Choose complete, non-overlapping moments within the requested duration range.
5. **Render.** Apply stable framing or full-frame fit, highlighted captions and audio normalization.
6. **Review.** Decode the result, check timestamps and inspect sampled visual evidence. Accepted results and uncertain drafts remain separate.

A screen recording or slide presentation can use full-frame fit to preserve content. A crop is used only when the evidence supports one. Selection and framing do not invent visible speaker identities.

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
