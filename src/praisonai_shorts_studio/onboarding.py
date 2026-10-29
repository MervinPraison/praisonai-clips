"""Presentation helpers for first-run readiness and the public example."""
from __future__ import annotations

import io
from pathlib import Path
import zipfile

EXAMPLE_FILES = ("clip.mp4", "captions.srt", "captions.ass", "words.json", "edl.json", "example.json")


def processing_issues(checks: dict, *, until: str = "render") -> list[str]:
    issues = []
    if not checks.get("openai_api_key_present"):
        issues.append("Connect an OpenAI API key to process your own recordings.")
    if not checks.get("ffmpeg") or not checks.get("ffprobe"):
        issues.append("Install FFmpeg and ffprobe for video processing.")
    if checks.get("ffmpeg"):
        if until == "render" and not checks.get("subtitle_filter"):
            issues.append("Use an FFmpeg build with subtitle rendering (libass).")
        if not checks.get("h264_encoder"):
            issues.append("Use an FFmpeg build with H.264 encoding.")
        if until == "render" and not checks.get("loudnorm_filter"):
            issues.append("Use an FFmpeg build with audio normalization.")
    return issues


def example_directory() -> Path:
    return Path(__file__).resolve().parent / "resources/demo"


def example_bundle(folder: Path) -> bytes:
    """Only publish the explicit generated example files, never directory contents."""
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in EXAMPLE_FILES:
            bundle.write(folder / name, name)
    return archive.getvalue()


def stage_label(stage: str) -> str:
    if stage == "evidence_ready":
        return "Evidence ready to review"
    if stage == "selection_ready":
        return "Moments ready to review"
    if stage == "complete":
        return "Review your results"
    if stage in {"created", "inspect", "normalize"}:
        return "Preparing your recording"
    if stage.startswith("transcribe-"):
        return "Creating the transcript"
    if stage.startswith("overview-"):
        return "Understanding the visuals"
    if stage.startswith("selection-"):
        return "Finding complete moments"
    if "-crop-" in stage:
        return "Choosing the framing"
    if "-render-" in stage:
        return "Rendering your clip"
    if stage.startswith("clip-"):
        return "Checking the result"
    return "Processing your recording"
