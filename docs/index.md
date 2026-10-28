---
template: home.html
hide:
  - navigation
  - toc
---
<div class="edition"><span>PRAISONAI CLIPS · 0.1.0</span><span>LOCAL VIDEO WORKFLOW</span><span>1080 × 1920</span></div>
<div class="hero" markdown>
<div markdown>
<p class="eyebrow">FROM THE FULL STORY TO THE MOMENT</p>
<h1>Long video.<br><em>Short story.</em></h1>
<p class="lede">Turn a full-length video into reviewed vertical clips. Keep the source, the measured captions, and the final say.</p>
<div class="actions"><a class="paper-button" href="getting-started/quickstart/">Make your first clip ↗</a><a class="paper-button secondary" href="guides/workflow/">Read the workflow</a></div>
</div>
<figure class="framing-diagram">
<svg viewBox="0 0 500 370" role="img" aria-labelledby="crop-title crop-desc"><title id="crop-title">From landscape source to portrait clip</title><desc id="crop-desc">A portrait crop inside a landscape source frame, with the original source preserved.</desc><rect x="20" y="60" width="460" height="260" class="source-frame"/><path d="M20 234 L135 120 L224 213 L314 145 L480 290" class="scene-line"/><circle cx="315" cy="116" r="24" class="scene-line"/><rect x="176" y="60" width="146" height="260" class="crop-frame"/><path d="M249 60V320 M176 147H322 M176 233H322" class="crop-grid"/><text x="20" y="42">01 / THE SOURCE · 16:9</text><text x="176" y="347">02 / THE CUT · 9:16</text></svg>
<figcaption>Framing diagram. Stable crop when supported by evidence; full-frame fit for slides and screen recordings.</figcaption>
</figure>
</div>
<div class="section-heading"><span class="eyebrow">THE EDITORIAL PROCESS</span><span>Three steps. Every cut accounted for.</span></div>
<div class="feature-grid" markdown>
<div markdown>
<span class="step">01 / FIND</span>
### Find a complete thought
Transcribe with measured word timestamps and inspect sampled frames. Choose self-contained moments from the longer recording.
</div>
<div markdown>
<span class="step">02 / FRAME</span>
### Make room for the story
Render vertical video with evidence-based framing, highlighted captions and normalized audio. Keep an explicit mapping to the source.
</div>
<div markdown>
<span class="step">03 / REVIEW</span>
### Keep the final say
Accepted clips and uncertain drafts stay separate. Preview, listen and refine the result before sharing it.
</div>
</div>
<div class="section-heading"><span class="eyebrow">AT YOUR DESK</span><span>Python · OpenAI · FFmpeg</span></div>
<div class="start-grid" markdown>
<div markdown>
## A local workflow.<br><em>An editable result.</em>
Run from the command line or use the local upload screen. OpenAI processes audio and sampled frames; jobs and output files stay in your local data directory.
[Install the prerequisites](getting-started/installation.md) · [Explore editor control](editors/index.md)
</div>
<div markdown>
```sh
# After installation and API key setup
praisonai-clips doctor
praisonai-clips run 'input/main video.mp4'

# Or open the local dashboard
streamlit run app.py
```
</div>
</div>
