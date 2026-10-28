"""First-run safety: no paid work before setup, and no private files in the example."""
from pathlib import Path
from unittest.mock import patch
import io
import zipfile

from streamlit.testing.v1 import AppTest

from praisonai_shorts_studio.onboarding import EXAMPLE_FILES, example_bundle, processing_issues, stage_label
from praisonai_shorts_studio.store import Store

ROOT = Path(__file__).resolve().parents[1]
READY = {"openai_api_key_present": True, "ffmpeg": "ffmpeg", "ffprobe": "ffprobe",
         "subtitle_filter": True, "loudnorm_filter": True, "h264_encoder": True}


def test_missing_subtitle_support_blocks_processing_before_paid_work():
    assert processing_issues(READY) == []
    assert any("subtitle" in issue for issue in processing_issues({**READY, "subtitle_filter": False}))
    assert any("ffprobe" in issue for issue in processing_issues({**READY, "ffprobe": None}))


def test_example_archive_only_contains_the_explicit_public_files(tmp_path):
    for name in EXAMPLE_FILES:
        (tmp_path / name).write_text("Generated test fixture")
    (tmp_path / "private-report.json").write_text("Must not be included")
    with zipfile.ZipFile(io.BytesIO(example_bundle(tmp_path))) as bundle:
        assert set(bundle.namelist()) == set(EXAMPLE_FILES)


def test_first_visit_example_works_without_processing_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("SHORTS_DATA_DIR", str(tmp_path))
    with patch("praisonai_shorts_studio.cli.doctor", return_value={}), patch("subprocess.Popen") as launch:
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
        assert not app.exception
        assert next(b for b in app.button if b.label == "Create my clips").disabled
        assert any(b.label == "Download the example bundle" for b in app.get("download_button"))
        assert not Store(tmp_path).list()
        launch.assert_not_called()


def test_ready_first_visit_still_requires_a_source(tmp_path, monkeypatch):
    monkeypatch.setenv("SHORTS_DATA_DIR", str(tmp_path))
    with patch("praisonai_shorts_studio.cli.doctor", return_value=READY), patch("subprocess.Popen") as launch:
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=20)
        assert not app.exception
        assert next(b for b in app.button if b.label == "Create my clips").disabled
        next(t for t in app.text_input if t.label == "Local video path").set_value(str(tmp_path))
        app.run()
        next(b for b in app.button if b.label == "Create my clips").click()
        app.run()
        assert not app.exception
        assert any("rather than a folder" in e.value for e in app.error)
        assert not Store(tmp_path).list()
        launch.assert_not_called()


def test_stages_show_the_action_instead_of_internal_cache_names():
    assert stage_label("transcribe-0000") == "Creating the transcript"
    assert stage_label("clip-01-render-1") == "Rendering your clip"
    assert stage_label("complete") == "Review your results"
