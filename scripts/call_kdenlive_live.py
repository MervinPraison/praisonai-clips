"""Call a live editor tool through standard MCP, with an explicit document guard.

Example: .venv/bin/python scripts/call_kdenlive_live.py --project /path/copy.kdenlive get_timeline_summary '{}'
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/kdenlive-live-api'))
from kdenlive_api import Resolve
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True,help='Expected currently open project; refuse any other document')
    parser.add_argument('tool')
    parser.add_argument('arguments',nargs='?',default='{}')
    args=parser.parse_args()
    service=(ROOT/'data/kdenlive-live-test/service.txt').read_text().strip()
    os.environ['KDENLIVE_DBUS_SERVICE']=service
    current=Path(Resolve()._dbus.get_project_path()).resolve()
    if current!=args.project.resolve():
        raise SystemExit(f'Refusing to edit another document: {current}')
    async with stdio_client(StdioServerParameters(command=str(ROOT/'scripts/kdenlive-live-mcp'),cwd=str(ROOT),env=dict(os.environ))) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            response=await session.call_tool(args.tool,json.loads(args.arguments))
            output='\n'.join(x.text for x in response.content if x.type=='text')
            print(output)
            if response.isError or 'ERROR:' in output:raise SystemExit(1)


if __name__=='__main__':asyncio.run(main())
