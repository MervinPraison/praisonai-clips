"""Publish the skill's maintained Resolve runbook without duplicating its source."""
from pathlib import Path
from mkdocs.structure.files import File


def on_files(files, config):
    root = Path(config.config_file_path).parent
    source = root / 'skills/resolve-mac-live/references/runbook.md'
    files.append(File.generated(config, 'editors/resolve-runbook.md', content=source.read_text()))
    report = root / 'M0_REPORT.md'
    files.append(File.generated(config, 'reference/validation-report.md', content=report.read_text()))
    return files
