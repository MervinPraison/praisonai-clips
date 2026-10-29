"""Local UI. Start with: streamlit run app.py"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from praisonai_shorts_studio.cli import doctor
from praisonai_shorts_studio.artifacts import clip_bundle
from praisonai_shorts_studio.onboarding import example_directory, example_bundle, processing_issues, stage_label
from praisonai_shorts_studio.pipeline import default_config, validate_config
from praisonai_shorts_studio.store import Store

load_dotenv()
st.set_page_config(page_title="PraisonAI Clips", page_icon="🎬", layout="wide")
store = Store(os.getenv("SHORTS_DATA_DIR", "data"))
style = (Path(__file__).resolve().parent / "assets/studio.css").read_text()
st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)
st.markdown('<div class="codex-credit">This project was built entirely using <strong>OpenAI Codex</strong>.</div>', unsafe_allow_html=True)
st.markdown('<div class="studio-masthead"><span>PRAISONAI CLIPS</span><span>YOUR CONTENT WORKSPACE</span></div>', unsafe_allow_html=True)
st.title("Turn your long videos into clips worth sharing.")
st.markdown('<p class="studio-intro">Find complete moments, add highlighted captions, and make vertical clips from interviews, lessons, webinars, and walkthroughs. Review the results and choose what to share.</p>', unsafe_allow_html=True)


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


def new_recording():
    checks = doctor()
    issues = processing_issues(checks)
    uploaded = st.file_uploader("Add your recording", type=["mp4", "mov", "mkv", "webm", "m4v"],
                                help="Upload up to 2 GB, or use a local file below.")
    with st.expander("Use a local file or adjust clip settings"):
        local_path = st.text_input("Local video path", placeholder="/path/to/video.mp4")
        maximum = st.slider("Maximum clips", 1, 5, 5)
        lengths = st.slider("Length range (seconds)", 5, 60, (30, 60))
    st.caption(f"Up to {maximum} clips · {lengths[0]}–{lengths[1]} seconds · Vertical video with captions")
    if issues:
        st.info("The example is ready to explore. Complete setup to process your own video.")
        with st.expander("Enable processing on this computer"):
            for issue in issues:
                st.write("• " + issue)
            if not checks.get("openai_api_key_present"):
                st.write("Add your key to the local .env file, then restart the app:")
                st.code("OPENAI_API_KEY=your-key", language="bash")
            if sys.platform == "darwin" and any("FFmpeg" in issue for issue in issues):
                st.code('brew install ffmpeg-full\nexport PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"\nstreamlit run app.py', language="bash")
            st.caption("The example uses no API calls. Processing your recording sends audio and sampled frames to OpenAI and is billed to your account.")
    st.caption("Your files and results stay in this workspace. Audio and sampled frames are sent to OpenAI for analysis; API charges apply.")
    if st.button("Create my clips", type="primary", use_container_width=True,
                 disabled=bool(issues) or (uploaded is None and not local_path.strip())):
        try:
            config = default_config(max_clips=maximum, min_duration=lengths[0], max_duration=lengths[1])
            validate_config(config)
            if uploaded is not None:
                content = uploaded.getbuffer()
                fingerprint = hashlib.sha256(content).hexdigest()
                source = store.root / "uploads" / (fingerprint + Path(uploaded.name).suffix.lower())
                source.parent.mkdir(exist_ok=True)
                if not source.exists():
                    source.write_bytes(content)
            else:
                source = Path(local_path).expanduser().resolve(strict=True)
                if not source.is_file():
                    raise ValueError("Choose a video file, rather than a folder")
            job_id = store.create(source, config)
            launch(job_id)
            st.session_state["selected_job"] = job_id
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    with st.expander("System checks"):
        st.json(checks)


def show_example():
    example = example_directory()
    st.caption("PLAYABLE EXAMPLE · NO API KEY NEEDED")
    st.subheader("See the result before you start")
    st.video(str(example / "clip.mp4"))
    st.caption("12-second silent example · Generated graphics and scripted captions. No AI selection or editorial review was run.")
    st.download_button("Download the example bundle", example_bundle(example),
                       file_name="praisonai-clips-example.zip", mime="application/zip",
                       use_container_width=True)
    with st.expander("Compare with the original & see what is included"):
        st.video(str(example / "source.mp4"))
        st.write("The 16-second generated source becomes a 12-second vertical clip. The example uses the app's renderer, caption export, and source mapping, with an authored edit and scripted word times.")
        st.write("Your bundle includes the MP4, SRT and ASS captions, source/output word timings, edit mapping, and an explanation of how the example was made.")


jobs = store.list()
if not jobs:
    create, preview = st.columns([1.35, 1], gap="large")
    with create, st.container(border=True):
        st.caption("YOUR FIRST CLIPS START HERE")
        st.subheader("Bring a recording. Find its best moments.")
        new_recording()
    with preview, st.container(border=True, key="first_example"):
        show_example()
    st.markdown('<div class="studio-divider"><p class="studio-label">WHAT YOU GET FROM EACH ACCEPTED CLIP</p></div>', unsafe_allow_html=True)
    for col, title, description in zip(
        st.columns(3),
        ["A video ready to review", "Captions you can keep", "Control over the final cut"],
        ["Vertical MP4 with highlighted captions and normalized audio. Preview and listen before sharing.",
         "Download SRT and ASS files alongside the video, with source and output word timings.",
         "Inspect review evidence and edit mappings. Uncertain candidates stay in drafts for a closer look."],
    ):
        with col:
            st.subheader(title)
            st.write(description)
    with st.expander("What happens after I upload?"):
        st.write("We prepare your recording, transcribe the audio, inspect sampled frames, and choose complete moments. Then we frame, caption, render, and review each candidate. Processing time and API costs depend on the recording; fewer clips may pass review than you request.")
    with st.expander("Can I finish the edit in my desktop editor?"):
        st.write("Optional integrations export editable Kdenlive source cuts or support live framing in Kdenlive and DaVinci Resolve. Live adapters are experimental and require separate setup.")
    st.stop()
with st.sidebar:
    st.header("Create another set of clips")
    new_recording()
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
    cols[0].metric("Status", job["status"].replace("_", " ").title())
    cols[1].metric("Current step", stage_label(job["stage"]))
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
                st.download_button("Download clip bundle", clip_bundle(folder),
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
