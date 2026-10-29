import argparse
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from praisonai_shorts_studio.live.cli import configure, execute
from praisonai_shorts_studio.live.models import ClipTarget, FRAMING_KEYS
from praisonai_shorts_studio.live.silence import apply_silence_plan, plan_silence
from praisonai_shorts_studio.store import digest_file

TARGET = ClipTarget('project','timeline','clip',1,1)


def test_plan_finds_quiet_region_and_checks_source(tmp_path, monkeypatch):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'fixture')
    info = {'source': str(source), 'source_fps': 30, 'timeline_rate': 30,
            'source_start': 300, 'source_end': 390, 'duration': 90, 'media_id': 'media', 'properties': {}}
    client = Mock()
    client.run_lua.return_value = {'result': info}
    process = Mock(returncode=0, stderr='silence_start: 0.5\nsilence_end: 1.5 | silence_duration: 1.0\n')
    monkeypatch.setattr('praisonai_shorts_studio.live.silence.subprocess.run', lambda *a, **k: process)
    plan = plan_silence(client, TARGET, padding=.1)
    assert plan['ranges'] == [[300, 318], [342, 390]]
    assert plan['removed_ranges'] == [[318, 342]]
    assert plan['removed_seconds'] == .8
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='Source changed'):
        apply_silence_plan(client, plan, timeline_name='Review')
    assert client.run_lua.call_count == 1


def test_inclusive_native_end_keeps_last_frame_and_guards_native_value(tmp_path, monkeypatch):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'fixture')
    client = Mock()
    client._clip_code.side_effect = lambda target, code: code
    client.run_lua.return_value = {'result': {'source': str(source), 'source_fps': 30,
        'timeline_rate': 30, 'source_start': 300, 'source_end': 389, 'duration': 90,
        'media_id': 'media', 'properties': {}}}
    monkeypatch.setattr('praisonai_shorts_studio.live.silence.subprocess.run',
                        lambda *a, **k: Mock(returncode=0, stderr='silence_start: 0.5\nsilence_end: 1.5\n'))
    plan = plan_silence(client, TARGET, padding=.1)
    assert plan['ranges'] == [[300, 318], [342, 390]]
    assert plan['source_end'] == 389
    client.run_lua.return_value = {'result': {'video_clips': 2, 'audio_clips': 2}}
    apply_silence_plan(client, plan, timeline_name='Review')
    code = client.run_lua.call_args.args[0]
    assert 'GetSourceEndFrame()==389' in code
    assert 'startFrame=342,endFrame=390' in code
    assert 'Unexpected appended clip duration' in code


def test_apply_checks_ranges_and_delegates_guarded_native_operation(tmp_path):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'fixture')
    plan = {'target': TARGET.__dict__, 'source': str(source), 'source_sha256': digest_file(source),
            'source_start': 300, 'source_end': 390, 'duration': 90, 'media_id': 'media',
            'ranges': [[300,318],[342,390]], 'removed_ranges': [[318,342]], 'removed_seconds': .8}
    client = Mock()
    client._clip_code.side_effect = lambda t,c: c
    client.run_lua.return_value = {'result': {'video_clips': 2, 'audio_clips': 2}}
    result = apply_silence_plan(client, plan, timeline_name='Review')
    assert result['review']['video_clips'] == 2
    code = client.run_lua.call_args.args[0]
    assert 'GetSourceStartFrame()==300' in code and 'startFrame=342,endFrame=390' in code
    assert 'timelineResolutionWidth' in code and 'original.ZoomX' in code
    assert client.run_lua.call_args.kwargs['expected_project_id'] == 'project'
    plan['ranges'] = [[300, 400]]
    with pytest.raises(ValueError, match='Invalid source ranges'):
        apply_silence_plan(client, plan, timeline_name='Review')


def test_yaml_and_cli_use_same_sdk_options(tmp_path):
    parser = configure(argparse.ArgumentParser())
    target = tmp_path / 'target.json'
    target.write_text(json.dumps(TARGET.__dict__))
    spec = tmp_path / 'edit.yaml'
    spec.write_text(f'command: plan-silence\ntarget: {target}\nthreshold_db: -30\nmin_silence: 0.5\npadding: 0.1\n')
    client = Mock()
    client.plan_silence.return_value = {'ranges': []}
    execute(parser.parse_args(['execute',str(spec)]),client)
    yaml_call = client.plan_silence.call_args
    execute(parser.parse_args(['plan-silence','--target',str(target),'--threshold-db','-30','--min-silence','0.5','--padding','0.1']),client)
    assert client.plan_silence.call_args == yaml_call
    spec.write_text('command: execute\nfile: evil.yaml\n')
    with pytest.raises(ValueError, match='Nested'):
        execute(parser.parse_args(['execute',str(spec)]),client)


def test_plan_detects_actual_generated_audio(tmp_path):
    import shutil
    import subprocess
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg unavailable')
    source = tmp_path / 'tone.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
                    "aevalsrc=if(between(t\\,1\\,2)\\,0\\,0.3*sin(2*PI*440*t)):s=48000:d=3",
                    str(source)], check=True)
    client = Mock()
    client._clip_code.side_effect = lambda target, code: code
    client.run_lua.return_value = {'result': {'source': str(source), 'source_fps': 30,
        'timeline_rate': 30, 'source_start': 0, 'source_end': 90, 'duration': 90,
        'media_id': 'media', 'properties': {}}}
    plan = plan_silence(client, TARGET, threshold_db=-35, min_silence=.5, padding=.1)
    assert len(plan['removed_ranges']) == 1
    assert .7 <= plan['removed_seconds'] <= .9
