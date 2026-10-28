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
<h1>One recording.<br><em>More worth sharing.</em></h1>
<p class="lede">Turn long videos into captioned vertical clips. Find the complete thought, frame it for the feed, and keep the final editorial decision.</p>
<div class="actions"><a class="paper-button" href="getting-started/quickstart/">Create your first clips ↗</a><a class="paper-button secondary" href="product/">Explore the product</a></div>
<p class="hero-note">Local dashboard & CLI · OpenAI analysis · Optional desktop editor control</p>
</div>
<div class="workflow-visual" markdown="0" aria-label="Illustrated workflow from a source recording to reviewed clips">
<div class="visual-topline"><span>THE CONTENT WORKFLOW</span><span>01 → 03</span></div>
<div class="source-card"><span class="eyebrow">01 / START WITH THE FULL STORY</span><div class="waveform" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><strong>Your recording</strong><span>Webinar · Interview · Lesson · Walkthrough</span></div>
<div class="review-line"><span>02 / FIND · FRAME · CAPTION · REVIEW</span><span aria-hidden="true">↓</span></div>
<div class="clip-illustrations"><div><span>03 / A COMPLETE THOUGHT</span><div class="illustrated-subject" aria-hidden="true"></div><strong>A moment<br>that stands alone.</strong></div><div><span>03 / KEEP THE CONTEXT</span><div class="illustrated-slide" aria-hidden="true"><i></i><i></i><i></i></div><strong>The detail<br>worth keeping.</strong></div></div>
<p class="visual-caption">Workflow illustration. Clip content and review results depend on your recording.</p>
</div>
</div>
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
- Python SDK, CLI, and eight Resolve MCP tools
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
