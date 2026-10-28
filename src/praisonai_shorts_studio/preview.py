"""Portable HTML preview. No API key or external assets are included."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

from .store import Store


STYLE = """
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif;background:#0c0e14;color:#f2f2f8}
*{box-sizing:border-box}body{margin:0 auto;max-width:1440px;padding:40px 32px}
a{color:#bcacff;text-decoration:none}a:hover{text-decoration:underline}
header{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:40px}
h1{font-size:clamp(28px,4vw,48px);letter-spacing:-1.5px;margin:8px 0}h2{font-size:24px;margin:32px 0 20px}
p{line-height:1.6;color:#a7aec1}.eyebrow{font-size:12px;letter-spacing:2px;color:#a997ff;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:24px}
.card{background:#171b26;border:1px solid #2a3040;border-radius:18px;overflow:hidden;max-width:420px}
video{display:block;width:100%;aspect-ratio:9/16;max-height:660px;background:#000}
.copy{padding:20px}.copy h3{font-size:18px;line-height:1.4;margin:10px 0 14px}.copy p{font-size:13px}
.badge{display:inline-block;font-size:11px;letter-spacing:1px;border:1px solid #3b6854;color:#9de2b6;padding:5px 9px;border-radius:20px}
.draft{border-color:#8d6b33;color:#f0cc8a}.downloads{display:flex;gap:16px;flex-wrap:wrap;font-size:13px}
.empty{border:1px dashed #383f55;border-radius:18px;padding:40px;background:#121620}
.status{border:1px solid #34394b;border-radius:12px;padding:16px 20px;font-size:14px;color:#c6cadd}
button{background:#a997ff;color:#100e18;border:0;border-radius:10px;padding:12px 18px;cursor:pointer;font-weight:700}
footer{margin-top:48px;border-top:1px solid #282e40;padding-top:24px;color:#818ba3;font-size:13px}
details{margin:32px 0}summary{cursor:pointer;color:#d2b57c}
@media(max-width:600px){body{padding:24px 16px}header{display:block}.status{margin-top:20px}}
"""


def generate(store: Store):
    preview = store.root / "preview"
    preview.mkdir(exist_ok=True)
    cards, drafts, statuses = [], [], []
    for job in store.list():
        folder = store.job_dir(job["id"])
        statuses.append(f"<div class='status'>{html.escape(Path(job['source']).name)}<br>"
                        f"{html.escape(job['status'])} · {html.escape(job['stage'])}</div>")
        manifest_path = folder / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        for accepted, target in [(True, cards), (False, drafts)]:
            for entry in manifest["accepted" if accepted else "drafts"]:
                clip = Path(entry["path"])
                relative = "../" + clip.relative_to(store.root).as_posix()
                base = quote(relative, safe="/.")
                edl = json.loads((clip / "edl.json").read_text())
                duration = sum(m["source_end"] - m["source_start"] for m in edl["mappings"])
                badge = "ACCEPTED" if accepted else "UNCERTAIN DRAFT"
                links = "".join(f"<a href='{base}/{name}' download>{label}</a>" for name, label in
                    [("video.mp4", "MP4 ↓"), ("captions.srt", "SRT ↓"), ("captions.ass", "ASS ↓"),
                     ("words.json", "Words ↓"), ("edl.json", "Edit data ↓"), ("review.json", "Review ↓")])
                if (clip / 'kdenlive' / 'editable.kdenlive').exists():
                    links += f"<a href='{base}/kdenlive/editable.kdenlive' download>Editable source cuts ↓</a>"
                target.append(f"""<article class='card'><video controls preload='metadata' playsinline src='{base}/video.mp4'></video>
<div class='copy'><span class='badge {'draft' if not accepted else ''}'>{badge}</span>
<h3>{html.escape(entry['title'])}</h3><p>{duration:.1f}s · 1080 × 1920 · Captions included</p>
<p>{html.escape(edl['rationale'])}</p><div class='downloads'>{links}</div></div></article>""")
    empty = "<div class='empty'><h3>Your Shorts will appear here</h3><p>Transcription, visual analysis, editing and review are in progress. This page refreshes while jobs run.</p></div>"
    active = any(j["status"] in {"running", "pending"} for j in store.list())
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>PraisonAI Clips · Preview</title>
<style>{STYLE}</style></head><body><header><div><div class='eyebrow'>PRAISONAI / CLIPS STUDIO</div>
<h1>From full video to Shorts.</h1><p>Automatic edits. Word-timed captions. Ready for your review.</p></div>
<button onclick='location.reload()'>Refresh previews ↻</button></header>
<div class='grid'>{''.join(statuses)}</div><h2>Accepted Shorts <span style='color:#8e97b0'>({len(cards)})</span></h2>
<div class='grid'>{''.join(cards) or empty}</div>
<details><summary>Uncertain drafts ({len(drafts)})</summary><p>These clips did not pass every acceptance check.</p>
<div class='grid'>{''.join(drafts)}</div></details>
<footer>Local preview · H.264 / AAC · No automatic publishing<br>Review combines full media decode and timestamp checks with sampled visual inspection. Listen before publishing.</footer>
<script>const active={str(active).lower()}; if(active) setInterval(()=>{{if(!Array.from(document.querySelectorAll('video')).some(v=>!v.paused))location.reload()}},15000);</script>
</body></html>"""
    tmp = preview / "index.tmp.html"
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(preview / "index.html")
    return preview / "index.html"
