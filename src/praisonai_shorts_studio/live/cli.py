"""Thin command-line bindings for every public Resolve SDK operation."""
import argparse
import json
import sys
from pathlib import Path

from .models import ClipTarget, Framing, FRAMING_KEYS
from .resolve import ResolveClient


def configure(parser):
    commands = parser.add_subparsers(dest='resolve_command', required=True)
    for name in ('status', 'project', 'timeline', 'get-framing', 'set-framing',
                 'restore-framing', 'plan-silence', 'apply-silence', 'execute', 'save', 'export-frame', 'run-lua', 'mcp'):
        command = commands.add_parser(name)
        if name == 'mcp':
            continue
        command.add_argument('--output', type=Path, help='Write JSON to a new file instead of stdout')
        if name == 'execute':
            command.add_argument('file', type=Path, help='YAML command specification')
        if name == 'plan-silence':
            command.add_argument('--target', type=Path, required=True)
            command.add_argument('--threshold-db', type=float, default=-25.0)
            command.add_argument('--min-silence', type=float, default=0.3)
            command.add_argument('--padding', type=float, default=0.08)
        if name == 'apply-silence':
            command.add_argument('--plan', type=Path, required=True)
            command.add_argument('--timeline-name', required=True)
        if name == 'timeline':
            command.add_argument('--track-index', type=int, default=1)
        if name in {'get-framing', 'set-framing', 'restore-framing'}:
            command.add_argument('--target', type=Path, required=True,
                                 help='JSON ClipTarget from timeline output, or a prior framing result')
        if name == 'set-framing':
            for field in FRAMING_KEYS:
                command.add_argument('--' + field.replace('_', '-'), type=float)
        if name == 'restore-framing':
            command.add_argument('--snapshot', type=Path, required=True,
                                 help='Prior set-framing JSON result; its before values are restored')
        if name in {'save', 'export-frame', 'run-lua'}:
            command.add_argument('--project-id', required=True)
        if name in {'export-frame', 'run-lua'}:
            command.add_argument('file', type=Path)
    return parser


def execute(args, client=None):
    name = args.resolve_command
    if name == 'execute':
        import yaml
        spec = yaml.safe_load(args.file.read_text())
        if not isinstance(spec, dict) or not isinstance(spec.get('command'), str):
            raise ValueError('YAML must contain a command and its options')
        command = spec['command']
        if command in {'execute', 'mcp'}:
            raise ValueError('Nested YAML execution and MCP serving are not supported in YAML')
        positional = {'run-lua': 'file', 'export-frame': 'file'}
        argv = [command]
        if command in positional:
            key = positional[command]
            if key not in spec:
                raise ValueError(f'{command} requires {key}')
            argv.append(str(spec[key]))
        for key, value in spec.items():
            if key == 'command' or key == positional.get(command):
                continue
            if not isinstance(key, str) or not isinstance(value, (str, int, float)) or isinstance(value, bool):
                raise ValueError('YAML options must be scalar strings or numbers')
            argv += ['--' + key.replace('_', '-'), str(value)]
        if args.output:
            if 'output' in spec:
                raise ValueError('Specify output either in YAML or on the CLI')
            argv += ['--output', str(args.output)]
        return execute(configure(argparse.ArgumentParser()).parse_args(argv), client)
    if name == 'mcp':
        from .mcp import main as serve
        return serve()
    # Reserve the output before editing: an existing snapshot must not be lost,
    # and a known unwritable destination must not cause an unrecorded edit.
    output = None
    if args.output:
        args.output = args.output.expanduser().resolve()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output = args.output.open('x')
    try:
        target = None
        if name in {'get-framing', 'set-framing', 'restore-framing', 'plan-silence'}:
            value = json.loads(args.target.read_text())
            target = ClipTarget(**value.get('target', value))
        client = client if client is not None else ResolveClient()
        if name == 'status':
            result = client.status()
        elif name == 'project':
            result = client.project_info()
        elif name == 'timeline':
            result = client.timeline_items(args.track_index)
        elif name == 'get-framing':
            from dataclasses import asdict
            result = {'target': asdict(target), 'framing': client.get_framing(target).to_dict()}
        elif name == 'set-framing':
            changes = {field: getattr(args, field) for field in FRAMING_KEYS if getattr(args, field) is not None}
            result = client.set_framing(target, **changes)
        elif name == 'restore-framing':
            snapshot = json.loads(args.snapshot.read_text())
            if ClipTarget(**snapshot['target']) != target:
                raise ValueError('Snapshot target differs from the requested clip')
            result = client.restore_framing(target, Framing(**snapshot['before']))
        elif name == 'plan-silence':
            result = client.plan_silence(target, threshold_db=args.threshold_db,
                                         min_silence=args.min_silence, padding=args.padding)
        elif name == 'apply-silence':
            result = client.apply_silence_plan(json.loads(args.plan.read_text()), timeline_name=args.timeline_name)
        elif name == 'save':
            result = {'saved': client.save_project(args.project_id)}
        elif name == 'export-frame':
            result = {'path': str(client.export_frame(args.project_id, args.file))}
        else:
            result = client.run_lua(args.file.read_text(), expected_project_id=args.project_id)
        serialized = json.dumps(result, indent=2) + '\n'
        if output:
            output.write(serialized)
        else:
            print(serialized, end='')
        return result
    finally:
        if output:
            output.close()


def main(argv=None):
    parser = configure(argparse.ArgumentParser(description=__doc__))
    try:
        execute(parser.parse_args(argv))
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
