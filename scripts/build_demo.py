"""Build the public, silent first-run example with FFmpeg; no API calls or private media.

Run with the project installed and subtitle/drawtext-enabled FFmpeg on PATH.
Caption times are deliberately scripted fixture data, not transcription results.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from praisonai_shorts_studio import captions, media
from praisonai_shorts_studio.models import EDL, Mapping, Word

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src/praisonai_shorts_studio/resources/demo"
PHRASES = [
    (2, "One recording can hold several useful stories.", "ONE RECORDING.", "MORE TO SHARE."),
    (6, "Choose one complete thought and keep its context.", "KEEP THE IDEA.", "KEEP THE CONTEXT."),
    (10, "Add clear captions, then review before you share.", "CAPTION THE MOMENT.", "MAKE IT YOURS."),
]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="clips-public-demo-") as temporary:
        work = Path(temporary)
        labels = {
            "brand": "PRAISONAI CLIPS / EXAMPLE",
            "footer": "SILENT EXAMPLE / SCRIPTED CAPTIONS",
            "intro": "START WITH A STORY.",
            "outro": "MAKE IT YOURS.",
        }
        for index, (_, _, top, bottom) in enumerate(PHRASES):
            labels[f"top{index}"] = top
            labels[f"bottom{index}"] = bottom
        for name, value in labels.items():
            (work / f"{name}.txt").write_text(value)

        def text(name, size, y, when=None, color="0x20211e"):
            result = (f"drawtext=textfile={name}.txt:font='DejaVu Sans':fontsize={size}:"
                      f"fontcolor={color}:x=(w-text_w)/2:y={y}")
            if when:
                result += f":enable='{when}'"
            return result

        filters = [
            "drawbox=x=40:y=40:w=1200:h=640:color=0xb8b7ab:t=2",
            "drawbox=x=100:y=142:w=1080:h=2:color=0xb8b7ab:t=fill",
            "drawbox=x=452:y=190:w=376:h=270:color=0xece7dc:t=fill",
            text("brand", 16, 96), text("footer", 11, 660, color="0x65665e"),
            text("intro", 30, 330, "lt(t,2)"),
            text("outro", 30, 330, "gte(t,14)"),
        ]
        words = []
        for index, (start, phrase, _, _) in enumerate(PHRASES):
            when = f"gte(t,{start})*lt(t,{start+4})"
            filters.extend([text(f"top{index}", 30, 270, when),
                            text(f"bottom{index}", 30, 345, when)])
            tokens = phrase.split()
            step = 3.6 / len(tokens)
            words.extend(Word(word=word, start=start+.15+i*step,
                              end=start+.15+(i+.85)*step)
                         for i, word in enumerate(tokens))
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0xf5f2e9:s=1280x720:r=30:d=16",
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "16",
            "-vf", ",".join(filters), "-c:v", "libx264", "-threads", "2", "-preset", "fast",
            "-crf", "20", "-c:a", "aac", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(work / "source.mp4"),
        ], cwd=work, check=True)
        output = work / "rendered"
        output.mkdir()
        edl = EDL(title="One recording, more to share", rationale="Scripted public onboarding example; not AI-selected",
                  mode="crop", mappings=[Mapping(source_start=2, source_end=14, output_start=0)])
        captions.export(output, words, edl)
        (output / "edl.json").write_text(edl.model_dump_json(indent=2))
        clip = media.render(work / "source.mp4", output, edl, lambda: None)
        defects = media.technical_review(clip, edl.duration, lambda: None)
        if defects:
            raise RuntimeError(defects)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", str(clip),
                        "-frames:v", "1", "-vf", "scale=360:640", str(work / "poster.jpg")], check=True)
        shutil.copy2(work / "source.mp4", DEST / "source.mp4")
        shutil.copy2(clip, DEST / "clip.mp4")
        shutil.copy2(work / "poster.jpg", DEST / "poster.jpg")
        for name in ["captions.srt", "captions.ass", "words.json", "edl.json"]:
            shutil.copy2(output / name, DEST / name)
        metadata = {
            "title": edl.title, "source_duration": 16, "clip_duration": edl.duration,
            "dimensions": [1080, 1920], "media": "generated graphics and silent audio",
            "word_timing_origin": "scripted demonstration timings; not measured transcription",
            "selection": "authored edit; no AI selection or analysis", "api_calls": 0,
            "technical_checks": "Full decode, dimensions, codecs, duration and A/V start checks passed",
            "editorial_review": "not performed; this example is not an accepted pipeline job",
        }
        (DEST / "example.json").write_text(json.dumps(metadata, indent=2)+"\n")
    print("Built and decoded the public example. No API calls or private source files used.")


if __name__ == "__main__":
    main()
