"""Publish the skill's maintained Resolve runbook without duplicating its source."""
from hashlib import sha256
from pathlib import Path
from mkdocs.structure.files import File


def _paper_stylesheet(config):
    source = Path(config.config_file_path).parent / 'docs/stylesheets/paper.css'
    content = source.read_text()
    digest = sha256(content.encode()).hexdigest()[:12]
    return f'stylesheets/paper.{digest}.css', content


def on_config(config):
    # GitHub Pages caches assets. A content-specific URL prevents an old stylesheet
    # from being reused with newly deployed HTML; keep one maintained CSS source.
    destination, _ = _paper_stylesheet(config)
    config.extra_css = [destination if str(path) == 'stylesheets/paper.css' else path
                        for path in config.extra_css]
    return config


def on_files(files, config):
    destination, content = _paper_stylesheet(config)
    files.append(File.generated(config, destination, content=content))
    root = Path(config.config_file_path).parent
    for asset in (root / "src/praisonai_shorts_studio/resources/demo").iterdir():
        if asset.is_file():
            files.append(File.generated(config, "assets/demo/" + asset.name, content=asset.read_bytes()))
    source = root / 'skills/resolve-mac-live/references/runbook.md'
    files.append(File.generated(config, 'editors/resolve-runbook.md', content=source.read_text()))
    report = root / 'M0_REPORT.md'
    files.append(File.generated(config, 'reference/validation-report.md', content=report.read_text()))
    return files
