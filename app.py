"""Local UI. Start with: streamlit run app.py"""
from __future__ import annotations

import fcntl
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from praisonai_shorts_studio.cli import doctor
from praisonai_shorts_studio.pipeline import default_config
from praisonai_shorts_studio.store import Store

load_dotenv()
st.set_page_config(page_title="PraisonAI Clips", page_icon="🎬", layout="wide")
store = Store(os.getenv("SHORTS_DATA_DIR", "data"))
style = (Path(__file__).resolve().parent / "assets/studio.css").read_text()
st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)
st.markdown('<div class="studio-masthead"><span>PRAISONAI CLIPS</span><span>YOUR CONTENT WORKSPACE</span></div>', unsafe_allow_html=True)
st.title("One recording. More worth sharing.")
st.markdown('<p class="studio-intro">Find the complete thought. Frame it for the feed. Turn your longer recordings into captioned vertical clips, with a review step before delivery.</p>', unsafe_allow_html=True)


def active(job_id):
    with (store.job_dir(job_id) / "worker.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except BlockingIOError:
            return True


def launch(job_id):
    log = store.job_dir(job_id) / "worker.log"
    with log.open("ab") as output:
        subprocess.Popen([sys.executable, "-m", "praisonai_shorts_studio.cli", "--data-dir", str(store.root),
                          "resume", job_id], stdout=output, stderr=output,
                         cwd=Path(__file__).resolve().parent, start_new_session=True)


with st.sidebar:
    st.header("Start with a recording")
    st.caption("An interview, lesson, webinar, or product walkthrough.")
    uploaded = st.file_uploader("Source video", type=["mp4", "mov", "mkv", "webm", "m4v"])
    local_path = st.text_input("Or enter a local video path", placeholder="/path/to/video.mp4")
    maximum = st.slider("Maximum clips", 1, 5, 5)
    lengths = st.slider("Length range (seconds)", 5, 60, (30, 60))
    st.caption("Video frames and audio are sent to OpenAI. API usage is billed to your account. No automatic publishing.")
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Add OPENAI_API_KEY to .env and restart this app to enable processing.")
    if st.button("Create clips", type="primary", disabled=not os.getenv("OPENAI_API_KEY")):
        try:
            if uploaded is not None:
                content = uploaded.getbuffer()
                fingerprint = hashlib.sha256(content).hexdigest()
                source = store.root / "uploads" / (fingerprint + Path(uploaded.name).suffix.lower())
                source.parent.mkdir(exist_ok=True)
                if not source.exists():
                    source.write_bytes(content)
            elif local_path:
                source = Path(local_path).expanduser().resolve(strict=True)
            else:
                raise ValueError("Upload a video or enter its local path")
            config = default_config(max_clips=maximum, min_duration=lengths[0], max_duration=lengths[1])
            job_id = store.create(source, config)
            launch(job_id)
            st.session_state["selected_job"] = job_id
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    with st.expander("System checks"):
        st.json(doctor())

jobs = store.list()
if not jobs:
    st.markdown('<p class="studio-label">FROM FULL RECORDING TO FINISHED MOMENTS</p>', unsafe_allow_html=True)
    for col, step, title, description in zip(
        st.columns(3),
        ["01 / FIND", "02 / PRODUCE", "03 / REVIEW"],
        ["Start with the full story", "Give the moment its format", "Keep the final say"],
        ["Upload a video or choose a local file in the sidebar. We use the transcript and sampled frames to select complete thoughts.",
         "Create portrait clips with measured word captions, normalized audio, and framing that accounts for the source.",
         "Preview accepted clips, inspect uncertain drafts, and download the video, captions, and edit data together."],
    ):
        with col, st.container(border=True):
            st.caption(step)
            st.subheader(title)
            st.write(description)
    st.markdown('<div class="studio-divider"><p class="studio-label">AUTOMATION WITH EDITORIAL CONTROL</p></div>', unsafe_allow_html=True)
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Your source. Your judgment. More to share.")
        st.write("Clips keep measured captions and source mappings. Automated review separates accepted results from uncertain drafts, so you can inspect the evidence and decide what to publish.")
    with right, st.container(border=True):
        st.markdown("**Your first session**")
        st.write("1. Add a recording in the sidebar.\n2. Choose clip count and duration.\n3. Create, preview, and download.")
        st.caption("Processing uses OpenAI and FFmpeg. API charges apply. Your recordings and outputs stay in the local workspace; audio and sampled frames are sent for analysis.")
    with st.expander("Continue in a desktop editor"):
        st.write("Optional integrations export editable Kdenlive source cuts or support live framing in Kdenlive and DaVinci Resolve. Live adapters are experimental and require separate setup.")
    st.stop()
ids = [j["id"] for j in jobs]
main_job_file = store.root / "main-job.txt"
if "selected_job" not in st.session_state and main_job_file.exists():
    st.session_state["selected_job"] = main_job_file.read_text().strip()
st.subheader("Your recordings")
selected = st.selectbox("Choose a recording", ids,
    index=ids.index(st.session_state.get("selected_job")) if st.session_state.get("selected_job") in ids else 0,
    format_func=lambda key: next(f"{j['id']} · {Path(j['source']).name}" for j in jobs if j["id"] == key))


@st.fragment(run_every="3s")
def dashboard(job_id):
    job = store.get(job_id)
    cols = st.columns(3)
    cols[0].metric("Status", job["status"])
    cols[1].metric("Current step", job["stage"])
    worker_active = active(job_id)
    if job["status"] in {"pending", "running"} and worker_active:
        if cols[2].button("Cancel job"):
            store.update(job_id, cancel=1)
            st.info("Cancellation requested. Completed analysis is retained for resume.")
    elif job["status"] != "completed":
        if cols[2].button("Resume job", disabled=not os.getenv("OPENAI_API_KEY")):
            launch(job_id)
            st.rerun(scope="fragment")
    if job["error"]:
        st.error(job["error"])
    if job["status"] == "running" and not worker_active:
        st.warning("The worker is no longer active. Resume to continue from cached analysis.")
    manifest_path = store.job_dir(job_id) / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        st.subheader(f"Accepted clips ({len(manifest['accepted'])})")
        if job["status"] == "completed" and not manifest["accepted"]:
            st.info("No clips passed all acceptance checks. Any uncertain renders are available below.")
        for entry in manifest["accepted"]:
            folder = Path(entry["path"])
            st.markdown("### " + entry["title"])
            video_col, info_col = st.columns([1, 2])
            video_col.video(str(folder / "video.mp4"))
            with info_col:
                st.caption("1080 × 1920 · H.264/AAC · burned-in captions")
                st.caption("Passed full decode and timestamp checks plus sampled visual review. Listen before publishing.")
                archive = io.BytesIO()
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                    for name in ["video.mp4", "captions.srt", "captions.ass", "words.json", "edl.json", "review.json"]:
                        z.write(folder / name, name)
                st.download_button("Download clip bundle", archive.getvalue(),
                                   file_name=folder.name + ".zip", mime="application/zip", key=str(folder))
                with st.expander("Review evidence & edit mappings"):
                    st.json(entry["review"])
        with st.expander(f"Uncertain drafts ({len(manifest['drafts'])})"):
            for entry in manifest["drafts"]:
                st.write(entry["title"])
                st.json(entry["review"])
                st.video(str(Path(entry["path"]) / "video.mp4"))
    if manifest_path.exists() and not worker_active:
        with st.expander("Edit source cuts in Kdenlive (optional)"):
            st.caption("Exports source cuts and caption sidecars. Use Kdenlive 26.04. This does not reproduce the FFmpeg caption burn-in, audio normalization, or framing, and does not control an open editor window.")
            runtime = Path(__file__).resolve().parent / "tools/runtime/node/bin/node"
            if st.button("Export editable source-cut projects", disabled=not runtime.exists()):
                try:
                    from praisonai_shorts_studio.kdenlive import export_job
                    with st.spinner("Exporting through Kdenlive MCP…"):
                        export_job(store, job_id)
                    st.success("Editable projects exported.")
                except Exception as exc:
                    st.error(str(exc))
            for path in store.job_dir(job_id).glob("*/clip-*/kdenlive/editable.kdenlive"):
                st.download_button(f"Download {path.parent.parent.name} Kdenlive project", path.read_bytes(),
                                   file_name=path.parent.parent.name + ".kdenlive", key=str(path))
                st.caption("Keep the normalized source at its current local path. Caption sidecars are in the clip’s kdenlive folder.")
    with st.expander("Job details"):
        st.json({k: v for k, v in job.items() if k != "config"})


dashboard(selected)
