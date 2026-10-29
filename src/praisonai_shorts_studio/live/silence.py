"""Detect quiet pauses and build a guarded, non-destructive Resolve review timeline."""
from __future__ import annotations

import math
from pathlib import Path
import re
import subprocess
from dataclasses import asdict

from .lua import lua_number, lua_string
from .models import ClipTarget
from ..store import digest_file


def plan_silence(client, target: ClipTarget, *, threshold_db=-25.0, min_silence=0.3, padding=0.08):
    for value in (threshold_db, min_silence, padding):
        lua_number(value)
    if not -100 <= threshold_db < 0 or min_silence <= 0 or padding < 0 or padding * 2 >= min_silence:
        raise ValueError('Use a negative dB threshold, positive duration, and padding under half the duration')
    code = client._clip_code(target, "local m=assert(c:GetMediaPoolItem(),'Clip has no source media'); "
        "return {timeline_rate=t:GetSetting('timelineFrameRate'),source_start=c:GetSourceStartFrame(),"
        "source_end=c:GetSourceEndFrame(),duration=c:GetDuration(),source=m:GetClipProperty('File Path'),"
        "media_id=m:GetUniqueId(),source_fps=m:GetClipProperty('FPS'),properties=c:GetProperties()}")
    info = client.run_lua(code, expected_project_id=target.project_id)['result']
    fps = float(info['timeline_rate'])
    if fps != 30 or float(info['source_fps']) != 30 or info['source_end'] - info['source_start'] != info['duration']:
        raise ValueError('Only unretimed 30 fps clips are supported for pause removal')
    source = Path(info['source']).expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError('Source media is not a file')
    before_hash = digest_file(source)
    proc = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-ss', str(info['source_start']/fps),
        '-t', str(info['duration']/fps), '-i', str(source), '-af',
        f'silencedetect=noise={threshold_db}dB:d={min_silence}', '-vn', '-f', 'null', '-'],
        capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError('FFmpeg could not analyze the source audio: ' + proc.stderr[-1000:])
    if digest_file(source) != before_hash:
        raise ValueError('Source changed while audio was analyzed')
    starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', proc.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', proc.stderr)]
    if len(ends) < len(starts):
        ends.append(info['duration']/fps)
    cut, ranges, cursor = [], [], info['source_start']
    for a, b in zip(starts, ends):
        first = max(cursor, info['source_start'] + math.ceil((a + padding) * fps))
        last = min(info['source_end'], info['source_start'] + math.floor((b - padding) * fps))
        if last <= first:
            continue
        if first > cursor:
            ranges.append([cursor, first])
        cut.append([first, last])
        cursor = last
    if cursor < info['source_end']:
        ranges.append([cursor, info['source_end']])
    return {'target': asdict(target), 'source': str(source), 'source_sha256': before_hash,
            'media_id': info['media_id'], 'fps': fps, 'source_start': info['source_start'],
            'source_end': info['source_end'], 'duration': info['duration'],
            'properties': info['properties'], 'ranges': ranges, 'removed_ranges': cut,
            'removed_seconds': sum(b-a for a,b in cut)/fps,
            'settings': {'threshold_db': threshold_db, 'min_silence': min_silence, 'padding': padding}}


def apply_silence_plan(client, plan, *, timeline_name):
    target = ClipTarget(**plan['target'])
    if not isinstance(timeline_name, str) or not timeline_name.strip():
        raise ValueError('A new review timeline name is required')
    if not plan['removed_ranges'] or not plan['ranges']:
        raise ValueError('No removable quiet pauses were found; no timeline was created')
    if digest_file(Path(plan['source'])) != plan['source_sha256']:
        raise ValueError('Source changed after analysis; create a new plan')
    start, end = plan['source_start'], plan['source_end']
    if any(type(plan[k]) is not int or plan[k] < 0 for k in ('source_start', 'source_end', 'duration')):
        raise ValueError('Invalid source bounds in plan')
    spans = [(int(a),int(b)) for a,b in plan['ranges']]
    if any(type(x) is not int for row in plan['ranges'] for x in row) or any(a < start or b > end or a >= b for a,b in spans) or any(spans[i][1] > spans[i+1][0] for i in range(len(spans)-1)):
        raise ValueError('Invalid source ranges in plan')
    parts = ','.join(f'{{mediaPoolItem=m,startFrame={a},endFrame={b}}}' for a,b in spans)
    from .models import FRAMING_KEYS
    saved = ','.join(f'{native}=original.{native}' for native in FRAMING_KEYS.values())
    code = client._clip_code(target, "assert(c:GetSourceStartFrame()=="+str(start)+" and c:GetSourceEndFrame()=="+str(end)+",'Clip bounds changed'); "
        "assert(c:GetDuration()=="+str(plan['duration'])+",'Clip duration changed'); "
        "local m=assert(c:GetMediaPoolItem()); assert(m:GetUniqueId()=="+lua_string(plan['media_id'])+",'Source changed'); "
        "assert(tonumber(t:GetSetting('timelineFrameRate'))==30 and tonumber(m:GetClipProperty('FPS'))==30,'Frame rate changed'); "
        "assert(m:GetClipProperty('File Path')=="+lua_string(plan['source'])+",'Source path changed'); "
        "local original=c:GetProperties(); local width=t:GetSetting('timelineResolutionWidth'); local height=t:GetSetting('timelineResolutionHeight'); "
        "local pool=guarded_project:GetMediaPool(); local review=assert(pool:CreateEmptyTimeline("+lua_string(timeline_name)+"),'Could not create review timeline (name may already exist)'); "
        "assert(guarded_project:SetCurrentTimeline(review),'Could not open review timeline'); "
        "assert(review:SetSetting('useCustomSettings','1') and review:SetSetting('timelineFrameRate','30'),'Could not set 30 fps'); "
        "assert(review:SetSetting('timelineResolutionWidth',tostring(width)) and review:SetSetting('timelineResolutionHeight',tostring(height)),'Could not match timeline resolution'); "
        "assert(tonumber(review:GetSetting('timelineFrameRate'))==30,'Unexpected timeline frame rate'); "
        "local added=assert(pool:AppendToTimeline({"+parts+"}),'Append failed'); "
        "local videos=review:GetItemListInTrack('video',1) or {}; local audio=review:GetItemListInTrack('audio',1) or {}; "
        "assert(#videos=="+str(len(spans))+" and #audio=="+str(len(spans))+",'Unexpected video/audio clip count'); "
        "for _,item in ipairs(videos) do assert(item:SetProperties({"+saved+"}),'Framing failed') end; "
        "return {timeline_name=review:GetName(),timeline_id=review:GetUniqueId(),video_clips=#videos,audio_clips=#audio,"
        "start=review:GetStartFrame(),finish=review:GetEndFrame()}")
    result = client.run_lua(code, expected_project_id=target.project_id)['result']
    return {'review': result, 'removed_seconds': plan['removed_seconds'], 'removed_ranges': plan['removed_ranges']}
