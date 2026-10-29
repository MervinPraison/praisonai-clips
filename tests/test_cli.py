"""CLI boundary checks: exports, installable examples and guarded live edits."""
import argparse
import json
from pathlib import Path
from unittest.mock import Mock
import zipfile

import pytest

from praisonai_shorts_studio import cli
from praisonai_shorts_studio.artifacts import CLIP_FILES
from praisonai_shorts_studio.live.cli import configure, execute
from praisonai_shorts_studio.live.models import Framing
from praisonai_shorts_studio.onboarding import EXAMPLE_FILES
from praisonai_shorts_studio.store import Store, write_json

TARGET = dict(project_id='project', timeline_id='timeline', clip_id='clip', track_index=1, clip_index=1)


def test_example_without_key_or_store_and_no_overwrite(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setattr(cli, 'load_dotenv', lambda: None)
    output = tmp_path / 'example.zip'
    cli.main(['--data-dir', str(tmp_path / 'unused'), 'example', '--output', str(output)])
    assert json.loads(capsys.readouterr().out)['path'] == str(output)
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == set(EXAMPLE_FILES)
        assert archive.read('clip.mp4')[:4] != b''
    original = output.read_bytes()
    with pytest.raises(SystemExit) as error:
        cli.main(['example', '--output', str(output)])
    assert error.value.code == 1
    assert output.read_bytes() == original
    assert not (tmp_path / 'unused').exists()


def test_artifacts_separate_drafts_and_reject_path_escape(tmp_path, capsys):
    store = Store(tmp_path / 'data')
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'synthetic')
    job = store.create(source, {})
    folder = store.job_dir(job) / 'drafts/clip-01'
    folder.mkdir(parents=True)
    for name in CLIP_FILES:
        (folder / name).write_text('{}')
    (folder / 'private.txt').write_text('excluded')
    write_json(store.job_dir(job) / 'manifest.json', {'accepted': [], 'drafts': [{'path': str(folder)}]})
    prefix = ['--data-dir', str(store.root)]
    output = tmp_path / 'draft.zip'
    with pytest.raises(SystemExit):
        cli.main(prefix + ['bundle', job, 'clip-01', '--output', str(output)])
    assert not output.exists()
    cli.main(prefix + ['bundle', job, 'clip-01', '--draft', '--output', str(output)])
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == set(CLIP_FILES)
    cli.main(prefix + ['artifact', job, 'clip-01', 'review.json', '--draft'])
    assert capsys.readouterr().out.rstrip().endswith('{}')
    (folder / 'review.json').unlink()
    (folder / 'review.json').symlink_to(folder / 'private.txt')
    # Symlink artifacts are refused rather than exporting unrelated data.
    (folder / 'review.json').unlink()
    (folder / 'review.json').symlink_to(source)
    with pytest.raises(SystemExit):
        cli.main(prefix + ['artifact', job, 'clip-01', 'review.json', '--draft'])


def test_doctor_exit_and_readiness_block_paid_job(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, 'doctor', lambda: {})
    with pytest.raises(SystemExit) as error:
        cli.main(['doctor', '--check'])
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)['ready'] is False
    pipeline = Mock()
    monkeypatch.setattr(cli, 'Pipeline', pipeline)
    with pytest.raises(SystemExit):
        cli.main(['--data-dir', str(tmp_path), 'run', 'missing.mp4'])
    pipeline.assert_not_called()
    assert not Store(tmp_path).list()


def test_resolve_snapshot_restoration_and_wrong_identity(tmp_path):
    parser = configure(argparse.ArgumentParser())
    target = tmp_path / 'target.json'
    target.write_text(json.dumps(TARGET))
    snapshot = tmp_path / 'snapshot.json'
    client = Mock()
    client.set_framing.return_value = {'target': TARGET, 'before': Framing().to_dict(),
                                      'after': Framing(zoom_x=1.2, zoom_y=1.2).to_dict()}
    execute(parser.parse_args(['set-framing', '--target', str(target), '--zoom-x', '1.2', '--zoom-y', '1.2', '--output', str(snapshot)]), client)
    assert client.set_framing.call_args.kwargs == {'zoom_x': 1.2, 'zoom_y': 1.2}
    client.restore_framing.return_value = {'restored': True}
    execute(parser.parse_args(['restore-framing', '--target', str(target), '--snapshot', str(snapshot)]), client)
    assert client.restore_framing.call_args.args[1] == Framing()
    client.reset_mock()
    target.write_text(json.dumps({**TARGET, 'clip_id': 'different'}))
    with pytest.raises(ValueError, match='Snapshot target'):
        execute(parser.parse_args(['restore-framing', '--target', str(target), '--snapshot', str(snapshot)]), client)
    client.restore_framing.assert_not_called()
    with pytest.raises(FileExistsError):
        execute(parser.parse_args(['set-framing', '--target', str(target), '--pan', '10', '--output', str(snapshot)]), client)
    client.set_framing.assert_not_called()


def test_root_cli_routes_resolve_and_kdenlive_without_pipeline(monkeypatch):
    import praisonai_shorts_studio.live.cli as resolve_cli
    import praisonai_shorts_studio.live.kdenlive_cli as kdenlive_cli
    resolve = Mock()
    kdenlive = Mock()
    monkeypatch.setattr(resolve_cli, 'execute', resolve)
    monkeypatch.setattr(kdenlive_cli, 'execute', kdenlive)
    cli.main(['resolve', 'timeline', '--track-index', '2'])
    assert resolve.call_args.args[0].track_index == 2
    cli.main(['kdenlive', '--connection', 'connection.json', 'set-framing', '7', '--x', '-10', '--y', '0', '--width', '1080', '--height', '1920'])
    assert kdenlive.call_args.args[0].clip_id == 7


def test_cli_processes_fixture_media_and_exports_result(tmp_path, monkeypatch, capsys):
    from test_pipeline import FixtureBackend
    from praisonai_shorts_studio import media
    from praisonai_shorts_studio.pipeline import Pipeline
    source = tmp_path / 'source.mp4'
    media.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
               'testsrc2=size=320x180:rate=30:duration=4', '-f', 'lavfi', '-i',
               'sine=frequency=440:sample_rate=48000:duration=4', '-c:v', 'libx264',
               '-threads', '2', '-preset', 'ultrafast', '-c:a', 'aac', source])
    backend = FixtureBackend()
    monkeypatch.setattr(cli, 'Pipeline', lambda store, job_id: Pipeline(store, job_id, backend))
    monkeypatch.setattr(cli, 'doctor', lambda: dict(openai_api_key_present=True, ffmpeg='ffmpeg',
                      ffprobe='ffprobe', subtitle_filter=True, loudnorm_filter=True, h264_encoder=True))
    prefix = ['--data-dir', str(tmp_path / 'data')]
    cli.main(prefix + ['run', str(source), '--max-clips', '1', '--min-duration', '1', '--max-duration', '3'])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result['accepted']) == 1
    assert 'Job:' in captured.err
    job_id = Store(tmp_path / 'data').list()[0]['id']
    cli.main(prefix + ['manifest', job_id])
    assert json.loads(capsys.readouterr().out) == result
    cli.main(prefix + ['bundle', job_id, 'clip-01', '--output', str(tmp_path / 'clip.zip')])
    with zipfile.ZipFile(tmp_path / 'clip.zip') as archive:
        assert set(archive.namelist()) == set(CLIP_FILES)
        assert json.loads(archive.read('edl.json'))['mode'] == 'fit'


def test_kdenlive_cli_delegates_native_framing_and_refuses_nan():
    from praisonai_shorts_studio.live.kdenlive_cli import configure, execute
    from praisonai_shorts_studio.live.kdenlive import LiveClient
    parser = configure(argparse.ArgumentParser())
    client = Mock()
    client.transform.return_value = {'clip_id': 7}
    args = parser.parse_args(['--connection', 'connection.json', 'set-framing', '7',
                              '--x', '-135', '--y', '-240', '--width', '1350', '--height', '2400'])
    execute(args, client)
    client.transform.assert_called_once_with(7, -135, -240, 1350, 2400)
    with pytest.raises(ValueError, match='finite'):
        LiveClient.__new__(LiveClient).transform(7, float('nan'), 0, 1080, 1920)
