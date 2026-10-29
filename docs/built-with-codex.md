# One recording. A small win worth sharing.

**This project was built entirely using OpenAI Codex**, under Mervin Praison’s direction—from implementation and debugging to tests, documentation, and deployment. It was prepared for the community-led [Cambridge Codex Community Challenge](https://cambridge-codex-workshop-guide.lilizhu.chatgpt.site/challenges.html).

The everyday task: take a long recording, find a complete thought, make a captioned vertical clip, and check it before sharing. PraisonAI Clips brings those steps into one local workflow.

<div class="challenge-facts" markdown>
<div markdown>
<span class="step">01 / WHAT I MADE</span>
### A recording-to-clips workflow
A local app that selects moments, frames vertical video, adds highlighted captions, and separates accepted clips from uncertain drafts.
</div>
<div markdown>
<span class="step">02 / WHAT I CHANGED</span>
### Show the result before setup
A playable example, a main-screen upload, and a setup check replaced an explanation-first opening with an immediate way to explore the output.
</div>
<div markdown>
<span class="step">03 / WHAT I CHECKED</span>
### Test the path to the first clip
Rendering, caption timing, review/repair, resume, and first-run guards have automated coverage. Browser checks cover example playback and downloads.
</div>
</div>

## Watch the walkthrough

<video class="challenge-video" controls playsinline preload="metadata" poster="../assets/challenge/after-onboarding.png" aria-label="Captioned product walkthrough: what was made, changed, and checked"><source src="../assets/challenge/walkthrough.mp4" type="video/mp4"><a href="../assets/challenge/walkthrough.mp4">Download the captioned walkthrough</a>.</video>

[Open the video directly](assets/challenge/walkthrough.mp4) · [Try the short example](index.md#see-example) · [Explore the code](https://github.com/MervinPraison/praisonai-clips)

The walkthrough records the local application and uses the public generated example. Its word timings and edit are scripted. It demonstrates the renderer, exported files, and first-run experience; it does not depict a new transcription or AI selection run. Real-provider and native-editor validation are documented separately below.

## The request behind the improvement

The request was to make the app understandable and convincing to a new user. The improvement put the upload beside a playable example and added setup checks before processing. The check covered browser playback, the downloadable example bundle, and automated first-run tests. The example uses generated media and scripted captions, so it does not demonstrate a fresh AI selection.

## The improvement you can see

The earlier first-run screen explained the workflow, but the upload lived in a sidebar and visitors could not inspect an example result. The revised screen puts an upload beside a playable clip and a downloadable bundle. It checks for an API key and compatible FFmpeg before enabling processing.

<div class="iteration-images">
<figure><img src="../assets/challenge/before-onboarding.png" alt="Earlier onboarding: explanatory cards with the upload in a sidebar" loading="lazy"><figcaption>Before: explain the workflow and ask the visitor to start from the sidebar.</figcaption></figure>
<figure><img src="../assets/challenge/after-onboarding.png" alt="Improved onboarding: main-screen upload beside a playable example and download" loading="lazy"><figcaption>After: show a result, make the upload visible, and check setup before processing.</figcaption></figure>
</div>

## What the checks establish

| Check | Evidence | Boundary |
| --- | --- | --- |
| Local automated suite | [Verification snapshot](assets/challenge/verification.json) and [test source](https://github.com/MervinPraison/praisonai-clips/tree/main/tests) | Optional runtime tests are skipped when their dependencies are absent. |
| End-to-end render, repair, and resume | [Pipeline regression](https://github.com/MervinPraison/praisonai-clips/blob/main/tests/test_pipeline.py) uses real FFmpeg output and a clearly labelled synthetic API backend | This test checks application behavior without paid provider calls. |
| Real-video processing | A four-minute validation produced three captioned candidates; one passed review and two remained uncertain drafts. [Read the report](reference/validation-report.md). | A recorded engineering run, rather than a general quality or acceptance-rate claim. |
| First-run behavior | [Onboarding regressions](https://github.com/MervinPraison/praisonai-clips/blob/main/tests/test_onboarding.py) check missing setup, missing input, invalid paths, and the example bundle’s explicit file list | No paid request is started by these tests. |
| Public website | The custom domain serves the example video, documentation, and code links over HTTPS | GitHub Pages hosts static pages. Process personal recordings in the local Streamlit app. |
| Native editor framing | [Kdenlive](KDENLIVE_LIVE_CONTROL.md) and [Resolve](RESOLVE_LIVE_CONTROL.md) reports record framing changes and restoration | Experimental, version-dependent integrations. |

Run the checks yourself:

```sh
python -m pip install -e '.[dev,live]'
pytest -q
```

FFmpeg must include subtitle rendering, audio normalization, and H.264 encoding. Tests for optional local editor runtimes may skip. The [Verify project workflow](https://github.com/MervinPraison/praisonai-clips/actions/workflows/verify.yml) repeats the portable suite on GitHub; it does not connect to a desktop editor or call OpenAI.

## What Codex contributed

The work happened through a cycle of requests, implementation, inspection, and revision: build the processing workflow, test it on real media, add guarded editor control, simplify the first visit, check privacy, and publish the site. The improvement above came from asking Codex to make the experience convincing to a new visitor, then checking the result with actual browser playback, a downloaded ZIP, and automated first-run tests.

The project uses OpenAI, FFmpeg, Streamlit, MkDocs Material, and optional editor integrations. Existing third-party code, fonts, and license notices retain their attribution.

## Try the small win

[Watch the generated example](index.md#see-example), [run the local app](getting-started/quickstart.md), or [inspect the SDK](reference/resolve-sdk.md). Your final publishing decision stays with you: preview the framing, check the captions, and listen to the clip.
