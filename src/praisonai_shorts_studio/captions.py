from __future__ import annotations

import json
from pathlib import Path

from .models import EDL, Word


def map_words(words: list[Word], edl: EDL):
    """Map provider timings and explicitly flagged estimates across cuts."""
    result = []
    for cut in edl.mappings:
        for w in words:
            if w.start >= cut.source_start - 1e-6 and w.end <= cut.source_end + 1e-6:
                result.append({"word": w.word, "source_start": w.start, "source_end": w.end,
                               "timing_source": w.timing_source,
                               "start": max(0, cut.output_start + w.start - cut.source_start),
                               "end": min(edl.duration, cut.output_start + w.end - cut.source_start)})
    return result


def clock(t: float, ass=False):
    # Round once before splitting fields, avoiding 00:00:60,000 at boundaries.
    unit = 100 if ass else 1000
    ticks = round(max(0, t) * unit)
    seconds, sub = divmod(ticks, unit)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if ass:
        return f"{hours}:{minutes:02}:{seconds:02}.{sub:02}"
    return f"{hours:02}:{minutes:02}:{seconds:02},{sub:03}"


def ass_escape(text):
    # Prevent transcription content becoming subtitle control sequences.
    return text.replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", " ").replace("\r", " ")


def groups(words):
    group = []
    for w in words:
        if group and (len(group) >= 5 or w["start"] - group[0]["start"] > 2.5
                      or len(" ".join(x["word"] for x in group) + " " + w["word"]) > 34
                      or w["start"] - group[-1]["end"] > 0.7):
            yield group
            group = []
        group.append(w)
        if w["word"].rstrip().endswith((".", "!", "?")):
            yield group
            group = []
    if group:
        yield group


def export(folder: Path, words: list[Word], edl: EDL):
    mapped = map_words(words, edl)
    if not mapped:
        raise ValueError("Selected clip has no measured word timings")
    (folder / "words.json").write_text(json.dumps(mapped, indent=2, ensure_ascii=False), encoding="utf-8")
    srt = []
    ass = ["""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,60,&H00FFFFFF,&H0000FFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,110,110,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
    for index, group in enumerate(groups(mapped), 1):
        start, end = group[0]["start"], group[-1]["end"]
        text = " ".join(w["word"].strip() for w in group)
        srt.append(f"{index}\n{clock(start)} --> {clock(end)}\n{text}\n")
        # Each measured word receives its own highlight interval; pauses stay unhighlighted.
        boundaries = sorted({start, end, *(w["start"] for w in group), *(w["end"] for w in group)})
        for a, b in zip(boundaries, boundaries[1:]):
            if b - a < 0.01:
                continue
            parts = []
            for word in group:
                active = word["start"] <= (a + b) / 2 < word["end"]
                color = "&H0000FFFF&" if active else "&H00FFFFFF&"
                parts.append("{\\c" + color + "}" + ass_escape(word["word"].strip()))
            ass.append(f"Dialogue: 0,{clock(a, True)},{clock(b, True)},Default,,0,0,0,," + " ".join(parts))
    (folder / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    (folder / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    return mapped
