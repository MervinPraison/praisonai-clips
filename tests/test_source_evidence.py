import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from praisonai_shorts_studio.evidence import in_window, mapped_windows, waveform
from praisonai_shorts_studio.store import Store

ROOT = Path(__file__).resolve().parents[1]


def test_window_includes_intersecting_words_and_only_sampled_frames():
    words = [{'word': 'edge', 'start': 4.8, 'end': 5.2}, {'word': 'later', 'start': 10.0, 'end': 10.3}]
    scenes = [{'time': 5}, {'time': 10}]
    assert in_window(words, scenes, 5, 10) == ([words[0]], [scenes[0]])


def test_mapping_keeps_timing_boundaries_and_missing_evidence_distinct():
    words = [{'word': 'crosses', 'start': 4.8, 'end': 5.2}]
    scenes = [{'time': 5, 'scene': 'A screen'}]
    peaks = [{'Source time (s)': 4.98, 'Peak amplitude': .2},
             {'Source time (s)': 5.0, 'Peak amplitude': .7}]
    rows = mapped_windows(words, scenes, peaks, 0, 10)
    assert [r['Transcript'] for r in rows] == ['crosses', 'crosses']
    assert rows[0]['Screen observations'] == 'No frame sampled'
    assert 'A screen' in rows[1]['Screen observations']
    assert [r['Peak amplitude (0–1)'] for r in rows] == [.2, .7]
    missing = mapped_windows(None, None, None, 0, 5)[0]
    assert missing['Transcript'] == missing['Screen observations'] == 'Not ready'
    assert missing['Peak amplitude (0–1)'] is None


def test_waveform_measures_tone_and_silence(tmp_path):
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg unavailable')
    audio = tmp_path / 'tone.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
        'aevalsrc=if(lt(t\\,1)\\,0.5*sin(2*PI*440*t)\\,0):s=8000:d=2', str(audio)], check=True)
    data = waveform(audio, 0, 2)
    assert max(p['Peak amplitude'] for p in data[:40]) > .4
    assert max(p['Peak amplitude'] for p in data[60:]) < .01
    assert data[-1]['Source time (s)'] >= 1.98
    with pytest.raises(ValueError):
        waveform(audio, 0, 31)


def test_dashboard_shows_existing_source_evidence(tmp_path, monkeypatch):
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg unavailable')
    monkeypatch.setenv('SHORTS_DATA_DIR', str(tmp_path))
    original = tmp_path / 'input.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:r=30:d=2',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', '-c:v', 'libx264', '-c:a', 'aac',
                    '-shortest', str(original)], check=True)
    store = Store(tmp_path)
    job_id = store.create(original, {})
    store.update(job_id, status='completed', stage='complete')
    folder = store.job_dir(job_id)
    shutil.copyfile(original, folder / 'source.mp4')
    (folder / 'timeline.json').write_text(json.dumps({'duration': 2.0}))
    (folder / 'transcript.json').write_text(json.dumps({'words': [{'word': 'Hello', 'start': .2, 'end': .5}]}))
    (folder / 'scenes.json').write_text(json.dumps([{'time': 0, 'scene': 'A black screen', 'visible_text': ''}]))
    with patch('praisonai_shorts_studio.cli.doctor', return_value={}):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
        next(c for c in app.checkbox if c.label == 'Open source evidence').check()
        app.run(timeout=20)
    assert not app.exception
    assert any('A black screen' in text.value for text in app.markdown)
    assert any('Transcript · word by word' in text.value for text in app.markdown)
    assert len(app.dataframe) == 2
    assert app.dataframe[0].value.iloc[0]['Word'] == 'Hello'
    mapped = app.dataframe[1].value.iloc[0]
    assert mapped['Transcript'] == 'Hello'
    assert 'A black screen' in mapped['Screen observations']
    assert mapped['Peak amplitude (0–1)'] > 0
    assert any('Peak per 20 ms' in caption.value for caption in app.caption)
