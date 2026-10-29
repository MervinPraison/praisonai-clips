# From one recording to a repeatable content workflow

PraisonAI Clips brings moment selection, vertical framing, captions, rendering, and review into one local application. It is built for creators, educators, and content teams working with longer recordings.

## The product opportunity

A useful moment in a long recording still needs a beginning and an ending, framing that preserves the subject, readable captions, and a final check. PraisonAI Clips automates these steps while keeping the edit traceable and leaving the final publishing decision with the operator.

The current product is a developer-oriented, locally operated application. It includes a dashboard, a command-line interface, and an extensible SDK. Hosted collaboration, billing, social publishing, and enterprise administration are outside the current implementation.

## What makes the workflow distinctive

| Product choice | Practical value | Implementation |
| --- | --- | --- |
| Transcript and visual analysis | Choose complete thoughts and account for what is on screen | Measured word timestamps, sampled frames, and validated candidate ranges |
| Review before acceptance | Keep uncertain output out of the accepted collection | Technical media checks, sampled visual review, and supported framing repair |
| Explicit edit provenance | Inspect how the clip relates to the original recording | Source/output word timings, edit mappings, and review artifacts |
| Editor integration | Continue refining framing in a desktop workflow | Kdenlive source-cut export and native Kdenlive/Resolve adapters |
| Reusable automation | Expose the same Resolve framing operations to different clients | Shared SDK validation across Python, CLI, and MCP |

## Evidence you can inspect

### End-to-end processing

A four-minute real-video validation produced three captioned 1080 × 1920 candidates. One passed the revised automated review; two remained uncertain drafts. All three passed the reported technical decode, dimensions, codec, and timing checks. The acceptance gate was retained when review evidence was insufficient.

Read the [initial validation report](reference/validation-report.md) for the recorded environment, defects fixed, review limitations, and test scope. This is a historical engineering run, not a production acceptance-rate benchmark.

### Live editor control

- **Kdenlive on macOS:** native framing, sequence selection, seeking, undo/redo, and saving were exercised through MCP. Rendered frames changed with the zoom and matched the baseline after restoration. See [the validation scope](KDENLIVE_LIVE_CONTROL.md#actual-mac-validation-28-october-2026).
- **DaVinci Resolve on macOS:** live zoom, pan, crop, frame export, and framing restoration were tested on the documented Free-edition setup. The SDK uses explicit project and clip identity guards. See [setup and limitations](RESOLVE_LIVE_CONTROL.md) and the [SDK reference](reference/resolve-sdk.md).

Editor adapters depend on the documented runtime versions and supported operations. Live edits do not automatically update the pipeline's edit mappings or review manifest.

## Walk through the product

1. [Install and check the environment](getting-started/installation.md).
2. [Process a recording you have permission to use](getting-started/quickstart.md), or launch `streamlit run app.py` for the dashboard.
3. Preview a candidate and inspect the captions, framing, and review result. Listen before publishing.
4. Download an accepted clip bundle with video, caption sidecars, and edit data.
5. On a disposable editor project, follow the [Resolve runbook](editors/resolve-runbook.md) to demonstrate a live framing change and restoration.

Source audio and sampled frames are sent to OpenAI, with API charges billed to the operator. Jobs and outputs are stored locally. Read [data handling](reference/public-release.md) before sharing a demo or diagnostic bundle.
