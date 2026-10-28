"""Actual live MCP edits on the isolated demo project, never the user's original."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools/kdenlive-live-api'),str(ROOT/'tools/kdenlive-live-mcp')]
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from praisonai_shorts_studio.store import digest_file,write_json
from kdenlive_api import Resolve

OUT=ROOT/'data/kdenlive-live-test'
DEMO=OUT/'live-demo.kdenlive'


def dbus_snapshot(dbus):
    tracks=dbus.get_all_tracks_info()
    return {'tracks':tracks,'clips':{str(t['id']):dbus.get_clips_on_track(int(t['id'])) for t in tracks}}


def video_clips(snapshot):
    return [c for t in snapshot['tracks'] if str(t.get('audio',False)).lower() not in ('true','1')
            for c in snapshot['clips'][str(t['id'])]]


async def main():
    service=(OUT/'service.txt').read_text().strip()
    os.environ['KDENLIVE_DBUS_SERVICE']=service
    dbus=Resolve()._dbus
    path=dbus.get_project_path()
    if Path(path).resolve()!=DEMO:
        raise ValueError('Refusing to edit another open document: '+str(path))
    report={'service':service,'project':str(DEMO),'operations':[],'success':False}
    source=ROOT/'input/main video.mp4'
    report['source_sha256_before']=digest_file(source)
    async with stdio_client(StdioServerParameters(command=str(ROOT/'scripts/kdenlive-live-mcp'),cwd=str(ROOT),env=dict(os.environ))) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            tools=await session.list_tools()
            report['discovered_tool_count']=len(tools.tools)
            async def call(name,arguments=None):
                result=await session.call_tool(name,arguments or {})
                text='\n'.join(c.text for c in result.content if c.type=='text')
                report['operations'].append({'name':name,'arguments':arguments or {},'text':text,'isError':result.isError})
                write_json(OUT/'live-validation.json',report)
                if result.isError or 'ERROR:' in text:
                    raise RuntimeError(name+': '+text)
                print(name+': '+text[:250],flush=True)
                return text
            await call('get_project_info')
            before=dbus_snapshot(dbus)
            clips=video_clips(before)
            assert len(clips)==1, 'Demo must start with one video clip'
            clip_id=int(clips[0]['id'])
            await call('seek_to',{'frame':300})
            assert dbus.get_position()==300
            async def screenshot(label):
                text=await call('screenshot_window',{'max_size':1440})
                image=text.splitlines()[0].strip()
                if Path(image).exists():
                    destination=OUT/(label+'.jpg');shutil.copyfile(image,destination)
                    report[label+'_image']=str(destination)
            await screenshot('before')
            await asyncio.sleep(2)
            await call('split_clip',{'clip_id':clip_id,'frame':300})
            after=dbus_snapshot(dbus)
            assert len(video_clips(after))==2, 'Split did not change the live timeline'
            assert sum(int(c['duration']) for c in video_clips(after))==sum(int(c['duration']) for c in clips)
            await screenshot('after_split')
            await asyncio.sleep(2)
            await call('undo')
            undone=dbus_snapshot(dbus)
            assert len(video_clips(undone))==1, 'Native undo did not restore one clip'
            await asyncio.sleep(2)
            await call('redo')
            redone=dbus_snapshot(dbus)
            assert len(video_clips(redone))==2, 'Native redo did not restore the split'
            await call('save_project',{'file_path':str(DEMO)})
            await call('render_frame',{'frame':300,'max_short_side':640})
            await screenshot('final')
            report.update({'before':before,'after_split':after,'after_undo':undone,'after_redo':redone,
                           'source_sha256_after':digest_file(source)})
            assert report['source_sha256_before']==report['source_sha256_after']
            report['success']=True
            write_json(OUT/'live-validation.json',report)
            print('Actual live timeline split, undo, redo and save PASSED.',flush=True)


if __name__=='__main__':
    asyncio.run(main())
