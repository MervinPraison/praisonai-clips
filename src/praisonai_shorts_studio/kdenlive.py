"""Optional editable source-cut export; the FFmpeg render remains authoritative."""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from . import captions, media
from .models import EDL, Mapping, Word
from .store import digest_file, write_json


ROOT = Path(__file__).resolve().parents[2]


def seconds_to_frame(seconds: float, fps=30):
    return int((Decimal(str(seconds))*fps).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def frame_mappings(edl: EDL):
    result, cursor = [], 0
    for cut in edl.mappings:
        start, end = seconds_to_frame(cut.source_start), seconds_to_frame(cut.source_end)
        if end <= start:
            raise ValueError('Cut is shorter than one project frame')
        result.append({'source_in':start, 'source_out':end, 'output_start':cursor,
            'source_start_seconds':start/30, 'source_end_seconds':end/30,
            'original_source_start_seconds':cut.source_start, 'original_source_end_seconds':cut.source_end,
            'rounding_start_seconds':start/30-cut.source_start,
            'rounding_end_seconds':end/30-cut.source_end})
        cursor += end-start
    return result


def export_clip(store, job_id, clip_folder: Path):
    clip_folder=clip_folder.resolve(strict=True)
    job_folder=store.job_dir(job_id).resolve()
    if not clip_folder.is_relative_to(job_folder):
        raise ValueError('Clip must belong to this job')
    node=ROOT/'tools/runtime/node/bin/node'
    if not node.exists() or not (ROOT/'scripts/kdenlive-mcp').exists():
        raise ValueError('Optional Kdenlive MCP runtime is not installed; see docs/KDENLIVE_MCP_HANDOVER.md')
    source=job_folder/'source.mp4'
    if not source.exists():
        raise ValueError('Normalized source is required for editable external-reference projects')
    edl=EDL.model_validate_json((clip_folder/'edl.json').read_text())
    mappings=frame_mappings(edl)
    output=clip_folder/'kdenlive'
    output.mkdir(exist_ok=True)
    rounded=edl.model_copy(update={'mappings':[Mapping(source_start=m['source_in']/30,
        source_end=m['source_out']/30,output_start=m['output_start']/30) for m in mappings]})
    words=[Word.model_validate(w) for w in json.loads((job_folder/'transcript.json').read_text())['words']]
    captions.export(output,words,rounded)
    write_json(output/'rounded-edl.json',rounded.model_dump())
    request={'source':str(source),'source_sha256':digest_file(source),
        'edl_sha256':digest_file(clip_folder/'edl.json'),'title':edl.title,'output':str(output),'mappings':mappings}
    write_json(output/'export-request.json',request)
    store.update(job_id,stage=f'{clip_folder.name}-kdenlive-export')
    media.run([node,ROOT/'scripts/kdenlive_export.mjs',output/'export-request.json'],lambda:store.check(job_id),cwd=ROOT)
    (output/'README.txt').write_text(
        'Editable source-cut timeline for Kdenlive 26.04.x. This is not live GUI control.\n'
        'Normalized source is an external reference and must remain at its current path.\n'
        'Captions are separate SRT/ASS sidecars, not inserted into the Kdenlive timeline.\n'
        'FFmpeg framing, audio normalization and caption burn-in are not reproduced by this editable source-cut export.\n'
        'Portrait project settings and exact rounded cuts are exported; visual GUI effect parity is not claimed.\n'
        'Use scripts/kdenlive-compatible, not the old system Kdenlive.\n',encoding='utf-8')
    return output/'editable.kdenlive'


def export_job(store, job_id):
    import fcntl
    folder=store.job_dir(job_id)
    with (folder/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        job=store.get(job_id)
        manifest=json.loads((folder/'manifest.json').read_text())
        paths=[]
        try:
            for clip in manifest['accepted']+manifest['drafts']:
                paths.append(str(export_clip(store,job_id,Path(clip['path']))))
            return paths
        finally:
            store.update(job_id,stage=job['stage'])
