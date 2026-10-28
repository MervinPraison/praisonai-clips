"""Guard and transport regressions; no GUI calls or real project edits."""
import json
from pathlib import Path
import re
import subprocess
from importlib.resources import files

import pytest

from praisonai_shorts_studio.live import (
    ClipTarget, Framing, MacOSConsoleTransport, ResolveClient, ResolveError, ResolveTransportError,
)
from praisonai_shorts_studio.live.lua import lua_string

FUSCRIPT = Path('/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fuscript')
TARGET = ClipTarget('project', 'timeline', 'clip', 1, 1)


class LuaRuntime:
    """Execute generated SDK code against disposable Lua native-object doubles."""
    def __init__(self, directory):
        self.directory = directory
        self.mutations = None
        self.properties = None

    def execute(self, code):
        from praisonai_shorts_studio.live.models import FRAMING_KEYS
        native = self.properties or {FRAMING_KEYS[k]: v for k,v in Framing().to_dict().items()}
        properties = '{' + ','.join(f'{k}={v}' for k,v in native.items()) + '}'
        source = files('praisonai_shorts_studio.live.resources').joinpath('bridge.lua').read_text()
        harness = '''
local mutations=0
local props=__PROPERTIES__
local clip={GetUniqueId=function() return 'clip' end, GetName=function() return 'test.mp4' end,
 GetProperties=function() local t={} for k,v in pairs(props) do t[k]=v end return t end,
 SetProperties=function(self,t) mutations=mutations+1; for k,v in pairs(t) do props[k]=v end return true end}
local timeline={GetUniqueId=function() return 'timeline' end,
 GetItemListInTrack=function() return {clip} end}
local project={GetUniqueId=function() return 'project' end, GetCurrentTimeline=function() return timeline end}
resolve={GetProjectManager=function() return {GetCurrentProject=function() return project end} end}
local m=assert(loadstring(SOURCE))('RLB_BRIDGE_TESTING')
local r=m.run_chunk({resolve=resolve},CODE)
print('REPLY:'..m.hex(m.fit_response(r,r.result,64)))
print('MUTATIONS:'..mutations)
print('PROPERTIES:'..m.hex(m.json(props)))
'''.replace('__PROPERTIES__',properties).replace('SOURCE',lua_string(source)).replace('CODE',lua_string(code))
        script = self.directory/'test.lua'
        script.write_text(harness)
        result = subprocess.run([str(FUSCRIPT),'-l','lua',str(script)],text=True,capture_output=True,check=True)
        self.mutations = int(re.search(r'MUTATIONS:(\d+)',result.stdout)[1])
        self.properties = json.loads(bytes.fromhex(re.search(r'PROPERTIES:([0-9a-f]+)',result.stdout)[1]))
        return json.loads(bytes.fromhex(re.search(r'REPLY:([0-9a-f]+)',result.stdout)[1]))


@pytest.fixture
def runtime(tmp_path):
    if not FUSCRIPT.exists():
        pytest.skip('Optional native Lua interpreter is absent')
    return LuaRuntime(tmp_path)


def test_sdk_framing_changes_execute_in_lua_and_record_restorable_values(runtime):
    client=ResolveClient(runtime)
    result=client.set_framing(TARGET,zoom_x=1.25,zoom_y=1.25,pan=40,crop_left=20)
    assert result['before']==Framing().to_dict()
    assert result['after']==Framing(zoom_x=1.25,zoom_y=1.25,pan=40,crop_left=20).to_dict()
    assert runtime.mutations==1
    restored=client.restore_framing(TARGET,Framing(**result['before']))
    assert restored['before']==result['after']
    assert restored['after']==result['before']


@pytest.mark.parametrize('target',[
    ClipTarget('another-project','timeline','clip',1,1),
    ClipTarget('project','another-timeline','clip',1,1),
    ClipTarget('project','timeline','another-clip',1,1),
    ClipTarget('project','timeline','clip',1,2),
    ClipTarget('project\"; error(\"injected\") --','timeline','clip',1,1),
])
def test_stale_or_injected_identity_never_reaches_native_setter(runtime,target):
    with pytest.raises(ResolveError):
        ResolveClient(runtime).set_framing(target,zoom_x=2)
    assert runtime.mutations==0


def test_lua_literal_round_trips_controls_quotes_and_unicode(runtime):
    value=''.join(map(chr,range(32)))+'127\x7f "\\ café →'
    assert runtime.execute('return '+lua_string(value))['result']==value


@pytest.mark.parametrize('changes',[{}, {'zoom_x':float('nan')},{'pan':float('inf')},
                                    {'zoom_x':True},{'zoom_y':0},{'crop_top':-1},{'rotation':5}])
def test_invalid_framing_is_rejected_before_contacting_transport(changes):
    class NoCalls:
        def execute(self,code):
            pytest.fail('Validation must happen before desktop access')
    with pytest.raises(ValueError):
        ResolveClient(NoCalls()).set_framing(TARGET,**changes)


def test_transport_does_not_accept_command_echo_as_a_reply(tmp_path,monkeypatch):
    monkeypatch.setattr('sys.platform','darwin')
    def runner(argv,**kwargs):
        return subprocess.CompletedProcess(argv,0,stdout=argv[-2],stderr='')
    monkeypatch.setattr(subprocess,'run',runner)
    with pytest.raises(ResolveTransportError,match='No Lua Console reply'):
        MacOSConsoleTransport(tmp_path).execute('return true')


def test_transport_timeout_does_not_retry_a_possible_edit(tmp_path,monkeypatch):
    monkeypatch.setattr('sys.platform','darwin')
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        raise subprocess.TimeoutExpired(argv,kwargs['timeout'])
    monkeypatch.setattr(subprocess,'run',runner)
    with pytest.raises(ResolveTransportError,match='inspect Resolve before retrying'):
        MacOSConsoleTransport(tmp_path).execute('possible_mutation()')
    assert len(calls)==1


@pytest.mark.parametrize('envelope',[{'ok':True,'truncated':True},{'result':True},{'ok':False,'error':'native rejected'}])
def test_failed_or_incomplete_envelopes_never_become_success(envelope):
    class Transport:
        def execute(self,code): return envelope
    with pytest.raises(ResolveError):
        ResolveClient(Transport()).status()


def test_injected_transport_needs_no_desktop_and_preserves_status_result():
    class Transport:
        def execute(self,code): return {'ok':True,'result':{'alive':True,'project':{'id':'test'}}}
    assert ResolveClient(Transport()).status()['project']['id']=='test'


@pytest.mark.parametrize('restore_fails',[False,True])
def test_live_verifier_compensates_for_unknown_edit_and_always_records_report(tmp_path,monkeypatch,restore_fails):
    pytest.importorskip('mcp')
    import asyncio
    from dataclasses import asdict
    import importlib.util
    from types import SimpleNamespace
    source=Path(__file__).resolve().parents[1]/'scripts/test_resolve_mac_live.py'
    spec=importlib.util.spec_from_file_location('live_verifier',source)
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    original=Framing().to_dict()
    state={'framing':dict(original),'setters':0}

    async def call(name,arguments=None):
        arguments=arguments or {}
        if name=='resolve_status':return {'project':{'id':'project'}}
        if name=='get_timeline_items':return {'result':[{'target':asdict(TARGET)}]}
        if name=='get_framing':return dict(state['framing'])
        if name=='set_framing':
            state['setters']+=1
            if state['setters']==1:
                state['framing'].update(arguments['changes'])
                raise ResolveTransportError('Reply lost after native edit')
            if restore_fails:raise ResolveTransportError('Project changed during restoration')
            state['framing']=dict(arguments['changes'])
            return {}
        if name=='export_frame':
            Path(arguments['path']).write_text(json.dumps(state['framing'],sort_keys=True))
        return {}

    monkeypatch.setattr(verifier,'call_tool',call)
    monkeypatch.setattr(verifier,'pixels',lambda path:Path(path).read_text())
    args=SimpleNamespace(project_id='project',timeline_name='review',timecode='01:00:10:00')
    with pytest.raises(ResolveTransportError):
        asyncio.run(verifier.test(args,tmp_path))
    assert state['setters']==2  # one requested change and one restoration; no blind retry
    report=json.loads((tmp_path/'report.json').read_text())
    assert report['success'] is False
    if not restore_fails:
        assert report['restored']==original
        assert state['framing']==original


def test_concurrent_transport_calls_do_not_interleave_desktop_input(tmp_path,monkeypatch):
    fcntl=pytest.importorskip('fcntl')
    monkeypatch.setattr('sys.platform','darwin')
    monkeypatch.setattr(subprocess,'run',lambda *args,**kwargs:pytest.fail('A competing call must not reach desktop input'))
    with (tmp_path/'console-control.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ResolveTransportError,match='in progress'):
            MacOSConsoleTransport(tmp_path).execute('possible_mutation()')
