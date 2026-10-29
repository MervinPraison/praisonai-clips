---
template: home.html
hide:
  - navigation
  - toc
---
<div class="edition"><span>PRAISONAI CLIPS</span><span>AI VIDEO REPURPOSING</span><span>CREATE · REVIEW · REFINE</span></div>
<div class="hero" markdown>
<div markdown>
<p class="eyebrow">YOUR RECORDING HAS MORE TO GIVE</p>
<h1>Your long video.<br><em>Your next short.</em></h1>
<p class="lede">Find complete moments in your interviews, lessons, and webinars. Turn them into vertical clips with highlighted captions, then review and choose what to share.</p>
<div class="actions"><a class="paper-button" href="getting-started/quickstart/">Make my first clips ↗</a><a class="paper-button secondary" href="#see-example">Watch the example</a></div>
<p class="hero-note">Watch the example without an API key. Process your own video in the local app.</p>
<p class="hero-note">Built entirely using OpenAI Codex and prepared for the Cambridge Codex Community Challenge. <a href="built-with-codex/">See what we made and checked ↗</a> · <a href="getting-started/codex/">Connect Codex to your editor ↗</a></p>
<div class="editor-support" aria-label="Experimental real-time editor integrations">
<span class="editor-support-label">REAL-TIME EDITING · EXPERIMENTAL</span>
<div class="editor-support-links"><a href="reference/resolve-sdk/"><img src="assets/editor-logos/davinci-resolve.png" alt="" width="36" height="36"><span>DaVinci Resolve ↗</span></a><a href="KDENLIVE_LIVE_CONTROL/"><img src="assets/editor-logos/kdenlive.png" alt="" width="36" height="36"><span>Kdenlive ↗</span></a></div>
</div>
</div>
<figure class="demo-showcase" id="see-example">
<div class="demo-heading"><span>SEE WHAT YOU CAN TAKE AWAY</span><span>00:12</span></div>
<video controls playsinline preload="metadata" poster="assets/demo/poster.jpg" aria-label="A twelve-second generated vertical clip with scripted word-highlight captions"><source src="assets/demo/clip.mp4" type="video/mp4">Your browser does not support embedded video. <a href="assets/demo/clip.mp4">Download the example clip</a>.</video>
<figcaption>Silent generated example with scripted captions. Rendered with the app's video and caption pipeline; no AI selection or editorial review was run.</figcaption>
<div class="demo-downloads"><a href="assets/demo/clip.mp4" download>Download the clip ↗</a><a href="assets/demo/source.mp4">Compare the original</a></div>
</figure>
</div>
<div class="section-heading"><span class="eyebrow">EDIT BY CHATTING WITH CODEX</span><span>See changes in your editor.</span></div>
<p>Ask Codex to adjust framing in DaVinci Resolve or Kdenlive while you watch. In Resolve, you can also create a review timeline with quiet pauses removed. The Python SDK, MCP tools, CLI and YAML commands share the same guarded operations. <a href="reference/resolve-sdk/">Explore live Resolve editing ↗</a></p>
<figure class="codex-flow"><img src="assets/illustrations/codex-resolve-flow.svg" alt="A Codex chat request passes through PraisonAI Clips MCP and SDK checks to DaVinci Resolve; the edit appears on screen and the result returns to Codex."><figcaption>From a request in Codex to a result you can review in Resolve.</figcaption></figure>
<div class="value-strip"><div><strong>Complete thoughts</strong><span>Transcript + visual context</span></div><div><strong>Review before delivery</strong><span>Accepted clips & separate drafts</span></div><div><strong>Keep editorial control</strong><span>Source mappings & editor tools</span></div></div>
<div class="section-heading"><span class="eyebrow">BUILT FOR THE RECORDINGS YOU ALREADY MAKE</span><span>One workflow. More places to start.</span></div>
<div class="feature-grid" markdown>
<div markdown>
<span class="step">FOR CREATORS</span>
### Let the moment stand alone
Find complete thoughts inside an interview or longer conversation. Give each clip its own beginning and ending.
</div>
<div markdown>
<span class="step">FOR EDUCATORS</span>
### Keep the explanation intact
Make short lessons from longer recordings. Preserve slides and screen content with full-frame fit when a crop would lose context.
</div>
<div markdown>
<span class="step">FOR CONTENT TEAMS</span>
### Make the handoff inspectable
Review the result, download the video and caption files, and keep the source mappings available for the next edit.
</div>
</div>
<div class="section-heading"><span class="eyebrow">FROM SOURCE TO SHORT</span><span>Automation with an editorial checkpoint.</span></div>
<div class="process-grid" markdown>
<div markdown>
<span class="step">01 / FIND</span>
### Choose a complete thought
Measured transcription and sampled frames inform moment selection. Candidate ranges respect sentence and duration constraints.
</div>
<div markdown>
<span class="step">02 / PRODUCE</span>
### Frame, caption, render
Create vertical video with a stable crop or full-frame fit, word-highlight captions, and normalized audio.
</div>
<div markdown>
<span class="step">03 / REVIEW</span>
### Check before accepting
Run technical checks and sampled visual review. Attempt supported framing repairs and keep uncertain results in drafts.
</div>
<div markdown>
<span class="step">04 / REFINE</span>
### Keep the final say
Preview, listen, and download. Explore experimental native framing in Kdenlive or DaVinci Resolve when the cut needs a human finish.
</div>
</div>
<div class="section-heading"><span class="eyebrow">WORKING SOFTWARE. INSPECTABLE EVIDENCE.</span><span>See what has been tested.</span></div>
<div class="start-grid proof-grid" markdown>
<div markdown>
## The workflow is running.<br><em>The evidence is open.</em>
Real-video processing has produced captioned vertical clips with explicit review outcomes. Native editor tests have verified live framing changes and restoration against exported frames.
[Explore the product and validation](product.md) · [Read the processing report](reference/validation-report.md)
</div>
<div class="evidence-card" markdown>
<span class="step">CURRENT PRODUCT · 0.1.0</span>
### Build on a working foundation
- Local dashboard, CLI, and resumable jobs
- Video, captions, edit mappings, and review artifacts
- Python SDK, CLI, YAML, and Resolve MCP tools
- Experimental Kdenlive and Resolve integrations

Live adapters have version constraints. Automated review uses sampled frames; inspect and listen before publishing.
</div>
</div>
<div class="section-heading"><span class="eyebrow">START WITH YOUR NEXT RECORDING</span><span>Python · OpenAI · FFmpeg</span></div>
<div class="start-grid" markdown>
<div markdown>
## Bring a video.<br><em>Find its next story.</em>
Start in the dashboard or run a job from the command line. OpenAI processes audio and sampled frames; job state and output files stay in your local workspace. API usage is billed to your account.
[Install the prerequisites](getting-started/installation.md) · [Read about data handling](reference/public-release.md)
</div>
<div markdown>
```sh
# After installation and API key setup
praisonai-clips doctor
praisonai-clips run '/absolute/path/to/video.mp4'

# Or open the local dashboard
streamlit run app.py
```
</div>
</div>
