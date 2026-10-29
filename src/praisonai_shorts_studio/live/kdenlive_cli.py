"""CLI for an already launched, guarded macOS Kdenlive bridge session."""
import json
from pathlib import Path

from .kdenlive import LiveClient


def configure(parser):
    parser.add_argument('--connection', type=Path, required=True,
                        help='Private connection.json from scripts/kdenlive-mac-live launch')
    commands = parser.add_subparsers(dest='kdenlive_command', required=True)
    for name in ('status', 'timelines', 'select-sequence', 'seek', 'set-framing', 'undo', 'redo', 'save'):
        command = commands.add_parser(name)
        if name == 'select-sequence':
            command.add_argument('index', type=int)
        elif name == 'seek':
            command.add_argument('frame', type=int)
        elif name == 'set-framing':
            command.add_argument('clip_id', type=int)
            for field in ('x', 'y', 'width', 'height'):
                command.add_argument('--' + field, type=float, required=True)
    return parser


def execute(args, client=None):
    client = client if client is not None else LiveClient(args.connection.expanduser())
    name = args.kdenlive_command
    if name == 'select-sequence':
        result = client.select_sequence(args.index)
    elif name == 'seek':
        result = client.seek(args.frame)
    elif name == 'set-framing':
        result = client.transform(args.clip_id, args.x, args.y, args.width, args.height)
    else:
        result = getattr(client, name)()
    print(json.dumps(result, indent=2))
    return result
