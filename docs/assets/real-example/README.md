# Real-video homepage example

The original is Mervin Praison’s public 14:02 YouTube tutorial,
[Chunking Strategies in RAG](https://www.youtube.com/watch?v=pIGRwMjhMaQ)
(`pIGRwMjhMaQ`). The local downloaded source lasted 841.68 seconds and had
SHA-256 `ebd18f433f2698f55f68098ea00f78fa128a40ed2d8f176856d86b18a9098d43`.
The full video stays on YouTube; it is not duplicated in this repository.

`short.mp4` is the 51.2-second output of job `9bf7975fa38c498f`, selected
from source time 0–51.17 seconds. The pipeline transcribed the full video,
described frames sampled at five-second intervals, selected five non-overlapping
candidates, rendered 1080 × 1920 videos, and exported captions. This example
uses full-frame fit to keep the slide visible. The selected range contained
no quiet pause that the pipeline removed.

All five videos passed technical checks but stayed as review drafts because
sampled visual review flagged possible caption defects. The frames inspected
for this example had readable captions; that spot check does not replace a
full visual and audio review. `captions.srt` accompanies the baked-in captions.
`poster.jpg` is a frame extracted from this output.
