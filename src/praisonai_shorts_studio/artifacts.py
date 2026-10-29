"""Shared read/export operations for the app and CLI. No processing or API calls."""
import io
import json
from pathlib import Path
import zipfile

CLIP_FILES = ('video.mp4', 'captions.srt', 'captions.ass', 'words.json', 'edl.json', 'review.json')


def manifest(store, job_id):
    store.get(job_id)
    return json.loads((store.job_dir(job_id) / 'manifest.json').read_text())


def clip_folder(store, job_id, clip_id, *, drafts=False):
    """Resolve an explicit manifest entry; never accept a caller-supplied path."""
    if not clip_id.startswith('clip-') or Path(clip_id).name != clip_id:
        raise ValueError('Use a clip ID from the manifest, such as clip-01')
    root = store.job_dir(job_id).resolve()
    for entry in manifest(store, job_id)['drafts' if drafts else 'accepted']:
        folder = Path(entry['path']).resolve(strict=True)
        if folder.name == clip_id:
            if not folder.is_relative_to(root):
                raise ValueError('Clip path escapes this job')
            return folder
    raise ValueError('Clip not found in ' + ('drafts' if drafts else 'accepted clips'))


def artifact_path(folder, name):
    if name not in CLIP_FILES:
        raise ValueError('Unknown clip artifact')
    folder = Path(folder).resolve(strict=True)
    if (folder / name).is_symlink():
        raise ValueError('Clip artifacts cannot be symlinks')
    source = (folder / name).resolve(strict=True)
    if source.parent != folder:
        raise ValueError('Clip artifact escapes its folder')
    return source


def clip_bundle(folder):
    archive = io.BytesIO()
    folder = Path(folder).resolve(strict=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name in CLIP_FILES:
            bundle.write(artifact_path(folder, name), name)
    return archive.getvalue()


def write_new(path, content):
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(content)
    return path
