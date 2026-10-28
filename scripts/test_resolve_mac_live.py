"""Opt-in real MCP framing test on an explicitly identified disposable timeline.

Leaves original framing restored, exports evidence, and saves the project.
Never chooses a project or timeline on the user's behalf.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from praisonai_shorts_studio.live import ClipTarget
from praisonai_shorts_studio.live.lua import lua_string
from praisonai_shorts_studio.live.mcp_client import call_tool


def pixels(path):
    data = subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-'])
    return hashlib.sha256(data).hexdigest()


async def test(args, out):
    status = await call_tool('resolve_status')
    if status.get('project',{}).get('id') != args.project_id:
        raise RuntimeError('Refusing a different project')
    result = await call_tool('get_timeline_items')
    # MCP wraps a root list in a result object; older protocol clients return the list directly.
    items = result.get('result',[]) if isinstance(result,dict) else result
    if len(items)!=1:
        raise RuntimeError('Use a disposable timeline with exactly one video clip')
    target = items[0]['target']
    ClipTarget(**target)
    checks = ("local t=assert(guarded_project:GetCurrentTimeline()); assert(t:GetUniqueId()=="+
              lua_string(target['timeline_id'])+"); assert(t:GetName()=="+lua_string(args.timeline_name)+"); "
              "assert(t:SetCurrentTimecode("+lua_string(args.timecode)+")); return true")
    await call_tool('run_lua',{'code':checks,'expected_project_id':args.project_id})
    before=await call_tool('get_framing',{'target':target})
    report={'status':status,'target':target,'original':before,'success':False}
    async def export(label):
        await call_tool('run_lua',{'code':checks,'expected_project_id':args.project_id})
        path=out/(label+'.png')
        await call_tool('export_frame',{'expected_project_id':args.project_id,'path':str(path)})
        return pixels(path)
    report['before_pixels']=await export('before')
    try:
        report['change']=await call_tool('set_framing',{'target':target,'changes':{
            'zoom_x':before['zoom_x']*1.25,'zoom_y':before['zoom_y']*1.25,
            'pan':before['pan']+40,'crop_left':before['crop_left']+20}})
        report['changed_pixels']=await export('changed')
    finally:
        # Restoration is compensation, not a retry of the requested mutation.
        try:
            await call_tool('set_framing',{'target':target,'changes':before})
            report['restored']=await call_tool('get_framing',{'target':target})
            report['restored_pixels']=await export('restored')
            await call_tool('save_project',{'expected_project_id':args.project_id})
        finally:
            (out/'report.json').write_text(json.dumps(report,indent=2))
    assert report['restored']==before
    assert report['before_pixels']!=report['changed_pixels'], 'The frame did not visibly change'
    assert report['before_pixels']==report['restored_pixels'], 'Restored pixels differ'
    report['success']=True
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'success':True,'evidence':str(out),'target':target},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--timeline-name',required=True)
    parser.add_argument('--timecode',default='01:00:10:00')
    parser.add_argument('--output',type=Path,default=Path('data/resolve-live'))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='sdk-test-',dir=args.output)).resolve()
    asyncio.run(test(args,out))


if __name__=='__main__':
    main()
