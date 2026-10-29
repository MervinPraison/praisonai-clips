from __future__ import annotations

import fcntl
import json
import math
import os
import re
from pathlib import Path

from . import captions, media, quiet
from .alignment import punctuate
from .ai import OpenAIBackend, PROMPT_VERSION
from .models import Candidate, CropChoice, EDL, Mapping, Scene, Word
from .review import inspect_render
from .store import Cancelled, Store, digest_file, write_json


def default_config(**overrides):
    return {"max_clips": 5, "min_duration": 30.0, "max_duration": 60.0,
            "vision_model": os.getenv("SHORTS_VISION_MODEL", "gpt-4o-mini"),
            "editor_model": os.getenv("SHORTS_EDITOR_MODEL", "gpt-4o-mini"),
            "transcription_model": os.getenv("SHORTS_TRANSCRIPTION_MODEL", "whisper-1"),
            "prompt_version": PROMPT_VERSION, **overrides}


def validate_config(config):
    if not 1 <= config["max_clips"] <= 5:
        raise ValueError("Choose between 1 and 5 Shorts")
    if not 1 <= config["min_duration"] <= config["max_duration"] <= 60:
        raise ValueError("Duration must satisfy 1 <= minimum <= maximum <= 60 seconds")


def sentence_end(word):
    return bool(re.search(r'[.!?][\s\"\u201d\u2019\')\]]*$', word.strip()))


def candidate_edl(candidate: Candidate, words: list[Word], config, duration):
    a, b = candidate.start_word, candidate.end_word
    if a > b or b >= len(words):
        raise ValueError("Out-of-range word indexes")
    if any(w.end <= w.start for w in words[a:b + 1]):
        raise ValueError("Clip includes words without a measured positive duration")
    if a and not sentence_end(words[a - 1].word):
        raise ValueError("Clip starts inside a sentence")
    if b != len(words) - 1 and not sentence_end(words[b].word):
        raise ValueError("Clip ends inside a sentence")
    # Padding stays inside adjacent words, so no partial neighboring word is included.
    start = max(0, words[a].start - 0.12, words[a - 1].end if a else 0)
    end = min(duration, words[b].end + 0.15,
              words[b + 1].start if b + 1 < len(words) else duration)
    if not config["min_duration"] <= end - start <= config["max_duration"]:
        raise ValueError("Clip duration is outside requested limits")
    return EDL(title=candidate.title, rationale=candidate.rationale,
               mappings=[Mapping(source_start=start, source_end=end, output_start=0)])


class Pipeline:
    def __init__(self, store: Store, job_id: str, backend=None):
        self.store, self.job_id = store, job_id
        self.folder = store.job_dir(job_id)
        self.job = store.get(job_id)
        self.config = json.loads(self.job["config"])
        validate_config(self.config)
        self.backend = backend
        self.check = lambda: store.check(job_id)

    def cache(self, name, inputs, compute):
        return self.store.cache(self.job_id, name,
            {"config": self.config, "source": self.job["fingerprint"], "inputs": inputs}, compute)

    def analysis_cache(self, name, model, inputs, compute):
        return self.store.shared_analysis(name, {
            "source_sha256": self.job["fingerprint"],
            "canonical_timeline_version": 1,
            "prompt_version": self.config["prompt_version"],
            "model": model,
            "inputs": inputs,
        }, compute)

    def frames(self, source, times, label):
        return [(t, media.frame(source, self.folder / "frames" / label / f"{t:.6f}.jpg", t, self.check))
                for t in times]

    def run(self, *, until="render"):
        if until not in {"evidence", "selection", "render"}:
            raise ValueError("Choose evidence, selection, or render")
        self.folder.mkdir(parents=True, exist_ok=True)
        # A second worker must not reset status or race completed artifacts.
        with (self.folder / "worker.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("This job already has an active worker")
            if self.store.get(self.job_id)["status"] == "completed":
                return json.loads((self.folder / "manifest.json").read_text())
            self.store.update(self.job_id, status="running", error=None)
            try:
                self.check()
                result = self.execute(until=until)
                if until == "render":
                    self.store.update(self.job_id, status="completed", stage="complete")
                else:
                    self.store.update(self.job_id, status="paused", stage=until + "_ready")
                return result
            except (Cancelled, KeyboardInterrupt):
                self.store.update(self.job_id, status="cancelled", error=None)
                return None
            except Exception as exc:
                # Do not persist SDK exception bodies (may contain user content or credentials).
                self.store.update(self.job_id, status="failed", error=type(exc).__name__ + ": " + str(exc)[:1200])
                raise

    def execute(self, *, until="render"):
        source = Path(self.job["source"])
        if digest_file(source) != self.job["fingerprint"]:
            raise ValueError("Source changed since job creation; create a new job")
        metadata = self.cache("inspect", {}, lambda: media.probe(source))
        canonical = self.folder / "source.mp4"
        if not canonical.exists():
            self.store.update(self.job_id, stage="normalize")
            media.normalize(source, canonical, metadata, self.check)
        meta = media.probe(canonical)
        duration = meta["duration"]
        write_json(self.folder / "timeline.json", {
            "version": 1, "unit": "seconds", "origin": "canonical source.mp4 presentation time zero",
            "original_file_start_time": metadata["start_time"],
            "original_timestamp_formula": "original_pts_seconds = canonical_seconds + original_file_start_time",
            "frame_quantization_seconds": 1 / 30,
            "notes": "Common FFmpeg input origin; CFR duplicates/drops may quantize frames by 1/30s. Initial audio gaps filled with silence.",
            "duration": duration, "source_sha256": self.job["fingerprint"], "metadata": metadata})
        self.check()
        if self.backend is None:
            self.backend = OpenAIBackend(self.config["vision_model"], self.config["editor_model"],
                                         self.config["transcription_model"])
        words = self.transcribe(canonical, duration)
        overview = self.overview(canonical, min(duration, meta["video_duration"]))
        if until == "evidence":
            return {"job_id": self.job_id, "stage": "evidence_ready", "words": len(words), "scenes": len(overview)}
        edls = self.select(words, overview, duration)
        write_json(self.folder / "selection.json", [e.model_dump() for e in edls])
        if until == "selection":
            return {"job_id": self.job_id, "stage": "selection_ready", "selections": [e.model_dump() for e in edls]}
        manifest = {"job_id": self.job_id, "source_sha256": self.job["fingerprint"],
                    "accepted": [], "drafts": [], "rejected_candidates": self.rejections,
                    "notes": [] if edls else ["No qualifying self-contained moments found."]}
        for i, edl in enumerate(edls):
            self.check()
            entry, accepted = self.make_clip(canonical, words, edl, i, meta)
            manifest["accepted" if accepted else "drafts"].append(entry)
            write_json(self.folder / "manifest.json", manifest)
        write_json(self.folder / "manifest.json", manifest)
        return manifest

    def transcribe(self, source, duration):
        combined = []
        # 600-second core plus 1 second on each edge: <=19.3 MB PCM WAV.
        for index, core in enumerate(range(0, math.ceil(duration), 600)):
            start = max(0, core - 1)
            end = min(duration, core + 601)
            audio = self.folder / f"audio-{index:04}.wav"
            def compute():
                media.extract_audio(source, audio, start, end - start, self.check)
                return self.backend.transcribe(audio)
            bounds = {"start": start, "end": end}
            raw = self.cache(f"transcribe-{index:04}", bounds,
                lambda: self.analysis_cache("transcription", self.config["transcription_model"], bounds, compute))
            for item in punctuate(raw.get("words", []), raw.get("text", "")):
                w = Word(word=item["word"], start=float(item["start"]) + start,
                         end=float(item["end"]) + start)
                if w.end > duration + 0.1:
                    raise ValueError("Transcriber returned timestamps outside source timeline")
                if core <= (w.start + w.end) / 2 < min(duration, core + 600):
                    combined.append(w)
        combined.sort(key=lambda w: w.start)
        alignment_warnings = []
        for index, word in enumerate(combined):
            if word.end == word.start:
                alignment_warnings.append({"word_index": index, "word": word.word,
                                           "provider_start": word.start, "provider_end": word.end})
                word.start = max(0, word.start - 0.04)
                word.end = min(duration, word.end + 0.04)
                if word.end <= word.start:
                    raise ValueError("Cannot estimate a positive interval for a zero-duration word")
                word.timing_source = "estimated_zero_duration"
        for previous, current in zip(combined, combined[1:]):
            overlap = previous.end - current.start
            if overlap <= 0.08:
                continue
            # Short provider overlaps can occur inside a transcription chunk too.
            # Split the shared interval without inventing a gap or changing order.
            boundary = (previous.end + current.start) / 2
            if overlap > 0.25 or boundary <= previous.start or boundary >= current.end:
                raise ValueError("Overlapping word measurements require manual alignment")
            alignment_warnings.append({"word": previous.word + " / " + current.word,
                                       "provider_previous_end": previous.end,
                                       "provider_current_start": current.start,
                                       "estimated_boundary": boundary})
            previous.end = boundary
            current.start = boundary
            previous.timing_source = current.timing_source = "estimated_overlap"
        if not combined:
            raise ValueError("No timed speech found")
        write_json(self.folder / "transcript.json", {"words": [w.model_dump() for w in combined],
                   "timing": "provider_measured_with_flagged_estimates_for_zero_duration_words",
                   "speaker_identity": None, "alignment_warnings": alignment_warnings,
                   "policy": "Zero-duration and short overlapping provider words receive flagged estimated intervals. Check captions before sharing."})
        return combined

    def overview(self, source, duration):
        times = [t for t in range(0, math.ceil(duration), 5) if t < duration - 0.05]
        scenes = []
        for index in range(0, len(times), 8):
            batch = times[index:index + 8]
            raw = self.cache(f"overview-{index:05}", batch,
                lambda: self.analysis_cache("screen-descriptions", self.config["vision_model"],
                    {"frame_times": batch, "frame_interval_seconds": 5},
                    lambda: self.backend.scenes(self.frames(source, batch, "overview"))))
            observations = [Scene.model_validate(s) for s in raw["scenes"]]
            requested = []
            for t in batch:
                matches = [s for s in observations if abs(s.time - t) <= 0.05]
                if len(matches) != 1:
                    raise ValueError("Visual observations do not match requested frame timestamps")
                requested.append(matches[0])
            # Ignore unrequested timestamps; they have no corresponding sampled frame.
            scenes.extend(s.model_dump() for s in requested)
        write_json(self.folder / "scenes.json", scenes)
        return scenes

    def select(self, words, scenes, duration):
        options = []
        for a in range(len(words)):
            if a and not sentence_end(words[a - 1].word):
                continue
            valid = []
            for b in range(a, len(words)):
                if words[b].end - words[a].start > self.config["max_duration"]:
                    break
                if words[b].end <= words[b].start:
                    break
                if b != len(words) - 1 and not sentence_end(words[b].word):
                    continue
                candidate = Candidate(start_word=a, end_word=b, title="", rationale="", score=1)
                try:
                    edit = candidate_edl(candidate, words, self.config, duration)
                    valid.append((candidate, edit))
                except ValueError:
                    continue
            # Keep diverse durations for each sentence start; bound long-video prompts.
            if len(valid) > 4:
                valid = [valid[0], valid[len(valid)//3], valid[2*len(valid)//3], valid[-1]]
            for c, e in valid:
                options.append({"option_id": len(options), "start_word": c.start_word,
                    "end_word": c.end_word, "start": e.mappings[0].source_start,
                    "end": e.mappings[0].source_end, "duration": round(e.duration, 3),
                    "text": " ".join(w.word for w in words[c.start_word:c.end_word + 1])})
        write_json(self.folder / "moment-options.json", options)
        candidates = []
        for start in range(0, math.ceil(duration), 120):
            end = min(duration, start + 180)
            local = [o for o in options if start <= o["start"] < end]
            if not local:
                continue
            evidence = {"min_duration": self.config["min_duration"], "max_duration": self.config["max_duration"],
                        "max_clips": self.config["max_clips"], "validated_moment_options": local,
                        "visual_evidence": [s for s in scenes if start <= s["time"] < end]}
            raw = self.cache(f"selection-options-{start:06}", evidence, lambda: self.backend.select(evidence))
            admissible = {o["option_id"]: o for o in local}
            for choice in raw["clips"]:
                option = admissible.get(choice["option_id"])
                if option:
                    candidates.append(Candidate(start_word=option["start_word"], end_word=option["end_word"],
                        title=choice["title"], rationale=choice["rationale"], score=choice["score"]))
        edls = []
        self.rejections = []
        for candidate in sorted(candidates, key=lambda c: c.score, reverse=True):
            if len(edls) >= self.config["max_clips"]:
                break
            try:
                if candidate.score < 0.65:
                    raise ValueError("Selection confidence below acceptance threshold")
                edl = candidate_edl(candidate, words, self.config, duration)
                m = edl.mappings[0]
                if any(max(m.source_start, e.mappings[0].source_start) <
                       min(m.source_end, e.mappings[0].source_end) for e in edls):
                    continue
                edls.append(edl)
            except ValueError as exc:
                self.rejections.append({"candidate": candidate.model_dump(), "reason": str(exc)})
        return edls

    def make_clip(self, source, words, edl, index, meta):
        label = f"clip-{index + 1:02}"
        draft = self.folder / "drafts" / label
        accepted_dir = self.folder / "accepted" / label
        # Resume after interruption between promotion and writing the manifest.
        if accepted_dir.exists():
            record = json.loads((accepted_dir / "review.json").read_text())
            if record.get("accepted"):
                return {"title": edl.title, "path": str(accepted_dir), "review": record}, True
            raise ValueError("Accepted output has no valid review")
        draft.mkdir(parents=True, exist_ok=True)
        cut = edl.mappings[0]
        dense_times = [min(cut.source_start + j * 0.5, cut.source_end - 0.05)
                       for j in range(math.ceil(edl.duration * 2))]
        crop_frames = self.frames(source, dense_times, label + "-dense")
        # Batch dense analysis, then require a consistent crop across every batch.
        choices = []
        for offset in range(0, len(crop_frames), 12):
            batch = crop_frames[offset:offset + 12]
            raw = self.cache(f"{label}-crop-{offset:03}",
                {"times": [t for t, _ in batch], "edl": edl.model_dump()},
                lambda: self.backend.crop(batch, {"source_width": meta["width"],
                    "source_height": meta["height"], "edl": edl.model_dump()}))
            choices.append(CropChoice.model_validate(raw))
        crop_width = min(1.0, meta["height"] * 9 / 16 / meta["width"])
        crop_height = min(1.0, meta["width"] * 16 / 9 / meta["height"])
        if (choices and all(c.mode == "crop" and c.confidence >= 0.85 for c in choices)
            and max(c.center_x for c in choices) - min(c.center_x for c in choices) < crop_width * 0.08
            and max(c.center_y for c in choices) - min(c.center_y for c in choices) < crop_height * 0.08):
            edl.mode = "crop"
            edl.crop_x = sum(c.center_x for c in choices) / len(choices)
            edl.crop_y = sum(c.center_y for c in choices) / len(choices)
        edl.crop_evidence = json.dumps([c.model_dump() for c in choices])
        edl.mappings = quiet.remove_quiet_pauses(source, cut, words, self.check)
        write_json(draft / "edl.json", edl.model_dump())
        mapped = captions.export(draft, words, edl)
        report = None
        for attempt in range(2):
            self.store.update(self.job_id, stage=f"{label}-render-{attempt}")
            # Render is repeatable; never use a partial render from a cancelled worker.
            video = media.render(source, draft, edl, self.check)
            def review_cache(name, inputs, compute):
                return self.cache(f"{label}-{attempt}-{name}", inputs, compute)
            report = inspect_render(source, video, draft, edl, mapped, self.backend, review_cache, self.check)
            report["attempt"] = attempt + 1
            accepted = report["accepted"]
            write_json(draft / f"review-attempt-{attempt + 1}.json", report)
            if accepted:
                break
            if attempt == 0 and edl.mode == "crop" and any(r["repair"] == "fit" for r in report["visual_reviews"]):
                edl.mode = "fit"
                edl.crop_evidence += "\nAutomatic repair: preserve whole source after crop review."
                write_json(draft / "edl.json", edl.model_dump())
                continue
            break
        self.check()
        write_json(draft / "review.json", report)
        if report["accepted"]:
            accepted_dir.parent.mkdir(exist_ok=True)
            draft.rename(accepted_dir)
            destination = accepted_dir
        else:
            destination = draft
        return {"title": edl.title, "path": str(destination), "review": report}, report["accepted"]
