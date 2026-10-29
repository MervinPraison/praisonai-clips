"""Validate a YAML workflow and map it to the same CLI operations."""
from __future__ import annotations

from pathlib import Path
import yaml


def workflow_arguments(path):
    path = Path(path).expanduser().resolve(strict=True)
    spec = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(spec, dict):
        raise ValueError('Workflow must be a YAML mapping')
    action = spec.get('action')
    if action not in ('run', 'resume'):
        raise ValueError('Workflow action must be run or resume')
    allowed = {'action', 'until', 'video', 'max_clips', 'min_duration', 'max_duration'} if action == 'run' else {'action', 'until', 'job_id'}
    if set(spec) - allowed:
        raise ValueError('Unknown workflow fields: ' + ', '.join(sorted(set(spec)-allowed)))
    until = spec.get('until', 'render')
    if until not in ('evidence', 'selection', 'render'):
        raise ValueError('until must be evidence, selection, or render')
    target = spec.get('video' if action == 'run' else 'job_id')
    if not isinstance(target, str) or not target.strip():
        raise ValueError('Workflow needs a video path or job_id')
    if action == 'run':
        video = Path(target).expanduser()
        target = str(video if video.is_absolute() else path.parent / video)
    args = [action, target, '--until', until]
    for key in ('max_clips', 'min_duration', 'max_duration'):
        if key in spec:
            if type(spec[key]) not in (int, float):
                raise ValueError(key + ' must be numeric')
            args.extend(['--' + key.replace('_', '-'), str(spec[key])])
    return args
