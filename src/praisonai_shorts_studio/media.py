from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


def run(args, check=lambda: None, cwd=None):
    """Bound memory usage, poll cancellation, and stop children on any interruption."""
    import tempfile
    with tempfile.TemporaryFile() as err:
        p = subprocess.Popen([str(a) for a in args], stdout=subprocess.DEVNULL,
                             stderr=err, cwd=cwd)
        try:
            while p.poll() is None:
                check()
                time.sleep(0.15)
            if p.returncode:
                err.seek(0)
                raise RuntimeError(f"{args[0]} failed: {err.read().decode(errors='replace')[-4000:]}")
        finally:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()


def probe(path: Path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                        "-of", "json", str(path)], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise ValueError(f"Cannot inspect video: {p.stderr[-1000:]}")
    data = json.loads(p.stdout)
    videos = [s for s in data["streams"] if s["codec_type"] == "video"
              and not s.get("disposition", {}).get("attached_pic")]
    audios = [s for s in data["streams"] if s["codec_type"] == "audio"]
    if not videos or not audios:
        raise ValueError("A source must contain video and audio")
    v = videos[0]
    duration = float(data["format"]["duration"])
    if duration <= 0:
        raise ValueError("Video has no positive duration")
    return {"duration": duration, "video_duration": float(v.get("duration", duration)), "width": v["width"], "height": v["height"],
            "start_time": float(data["format"].get("start_time", 0)),
            "video_stream": v["index"], "audio_stream": audios[0]["index"],
            "video_codec": v["codec_name"], "audio_codec": audios[0]["codec_name"],
            "streams": data["streams"]}


def normalize(source, target, metadata, check):
    """One canonical CFR timeline for audio, pictures, words and edit mappings.

    FFmpeg subtracts the common input origin by default. fps start_time=0 and
    aresample first_pts=0 fill initial gaps rather than shifting streams separately.
    """
    tmp = target.with_name("source.partial.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-threads", "2", "-i", source,
         "-map", f"0:{metadata['video_stream']}", "-map", f"0:{metadata['audio_stream']}",
         "-vf", "fps=fps=30:start_time=0,scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
         "-af", "aresample=48000:async=1:first_pts=0", "-c:v", "libx264", "-threads", "2",
         "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", tmp], check)
    probe(tmp)
    tmp.replace(target)


def extract_audio(source, target, start, duration, check):
    run(["ffmpeg", "-y", "-v", "error", "-ss", start, "-i", source, "-t", duration,
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", target], check)


def frame(source, target, timestamp, check=lambda: None):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        run(["ffmpeg", "-y", "-v", "error", "-threads", "1", "-ss", f"{timestamp:.6f}",
             "-i", source, "-frames:v", "1", "-vf", "scale=768:-2", "-threads", "1", target], check)
    if not target.exists() or not target.stat().st_size:
        raise RuntimeError(f"Could not extract frame at {timestamp}")
    return target


def render(source, folder, edl, check, width=1080, height=1920):
    m = edl.mappings[0]
    if edl.mode == "fit":
        framing = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black")
    else:
        framing = (f"crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':"
                   f"x='max(0,min(iw-ow,iw*{edl.crop_x}-ow/2))':"
                   f"y='max(0,min(ih-oh,ih*{edl.crop_y}-oh/2))',scale={width}:{height}")
    tmp = folder / "render.partial.mp4"
    # Use a fixed local subtitle filename, so uploaded names never enter a filter graph.
    parts = []
    for i, cut in enumerate(edl.mappings):
        parts.append(f'[0:v]trim=start={cut.source_start:.6f}:end={cut.source_end:.6f},setpts=PTS-STARTPTS[v{i}]')
        parts.append(f'[0:a]atrim=start={cut.source_start:.6f}:end={cut.source_end:.6f},asetpts=PTS-STARTPTS[a{i}]')
    inputs = ''.join(f'[v{i}][a{i}]' for i in range(len(edl.mappings)))
    parts.append(f'{inputs}concat=n={len(edl.mappings)}:v=1:a=1[joinedv][joineda]')
    parts.append('[joinedv]' + framing + ',setsar=1,ass=captions.ass[outv]')
    parts.append('[joineda]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[outa]')
    run(["ffmpeg", "-y", "-v", "error", "-threads", "2", "-i", source,
         "-filter_complex", ';'.join(parts), "-map", "[outv]", "-map", "[outa]",
         "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "20", "-r", "30",
         "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
        check, cwd=folder)
    tmp.replace(folder / "video.mp4")
    return folder / "video.mp4"


def technical_review(path, expected, check):
    meta = probe(path)
    defects = []
    if (meta["width"], meta["height"]) != (1080, 1920):
        defects.append("Incorrect output dimensions")
    if abs(meta["duration"] - expected) > 0.2:
        defects.append("Output duration differs from edit timeline")
    if meta["video_codec"] != "h264" or meta["audio_codec"] != "aac":
        defects.append("Unexpected output codecs")
    streams = meta["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    a = next(s for s in streams if s["codec_type"] == "audio")
    if abs(float(v.get("start_time", 0)) - float(a.get("start_time", 0))) > 0.1:
        defects.append("Audio/video start times differ")
    run(["ffmpeg", "-v", "error", "-xerror", "-i", path, "-f", "null", "-"], check)
    return defects
