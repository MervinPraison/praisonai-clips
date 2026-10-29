import json

import pytest

from praisonai_shorts_studio import captions, media, quiet
from praisonai_shorts_studio.models import EDL, Mapping, Word


def test_detect_and_render_quiet_cut_with_synced_word_timings(tmp_path):
    source = tmp_path / 'source.mp4'
    media.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30:duration=4', '-f', 'lavfi', '-i',
        "sine=frequency=440:sample_rate=48000:duration=4,volume=volume='if(between(t,1,2),0,1)':eval=frame",
        '-c:v', 'libx264', '-threads', '2', '-preset', 'ultrafast', '-c:a', 'aac', source])
    words = [Word(word='Before', start=.3, end=.7), Word(word='After.', start=2.3, end=2.7)]
    original = Mapping(source_start=0, source_end=4, output_start=0)
    mappings = quiet.remove_quiet_pauses(source, original, words, lambda: None)
    assert len(mappings) == 2
    assert mappings[0].source_end < mappings[1].source_start
    edit = EDL(title='Test', rationale='Test', mappings=mappings)
    mapped = captions.export(tmp_path, words, edit)
    assert mapped[1]['start'] == pytest.approx(2.3 - (mappings[1].source_start - mappings[0].source_end))
    output = media.render(source, tmp_path, edit, lambda: None, width=360, height=640)
    assert media.probe(output)['duration'] == pytest.approx(edit.duration, abs=.15)
    assert json.loads((tmp_path / 'words.json').read_text()) == mapped


def test_quiet_cut_protects_timed_word(monkeypatch):
    class Result:
        returncode = 0
        stderr = 'silence_start: 1.0\nsilence_end: 3.0 | silence_duration: 2.0\n'
    monkeypatch.setattr(quiet.subprocess, 'run', lambda *a, **kw: Result())
    word = Word(word='quiet', start=1.8, end=2.2)
    mappings = quiet.remove_quiet_pauses('source', Mapping(source_start=0, source_end=4, output_start=0), [word], lambda: None)
    assert any(m.source_start <= word.start and m.source_end >= word.end for m in mappings)
