"""Optional live adapter regression tests; no editor connection is made."""
from pathlib import Path
import sys

import pytest

API=Path(__file__).resolve().parents[1]/'tools/kdenlive-live-api'
pytestmark=pytest.mark.skipif(not API.exists(),reason='Optional live API checkout is absent')


def client_class():
    sys.path.insert(0,str(API))
    from kdenlive_api.dbus_client import KdenliveDBus
    return KdenliveDBus


def test_dbus_scalars_preserve_types_and_failed_edits_are_false():
    cls=client_class()
    assert cls._parse_scalar('boolean false')==(False,True)
    assert cls._parse_scalar('boolean true')==(True,True)
    assert cls._parse_scalar('int32 300')==(300,True)
    assert cls._parse_scalar('double 29.97')==(29.97,True)
    assert cls._parse_scalar('string "source.mp4"')==('source.mp4',True)
    client=cls.__new__(cls)
    client._call=lambda *args:cls._parse_dbus_send_output('method return time=0\n   boolean false')
    assert client.cut_clip(1,300) is False


def test_track_variant_map_preserves_video_boolean():
    text='''method return time=0
   array [
      variant          array [
            dict entry(
               string "id"
               variant                   int32 7
            )
            dict entry(
               string "audio"
               variant                   boolean false
            )
         ]
   ]'''
    assert client_class()._parse_dbus_send_output(text)==[{'id':7,'audio':False}]


def test_explicit_instance_prevents_arbitrary_service_selection(monkeypatch):
    cls=client_class()
    client=cls.__new__(cls)
    monkeypatch.setenv('KDENLIVE_DBUS_SERVICE','org.kde.kdenlive-2')
    assert client._discover_service()=='org.kde.kdenlive-2'
    monkeypatch.setenv('KDENLIVE_DBUS_SERVICE','org.some.other.app')
    with pytest.raises(ValueError):client._discover_service()


def test_live_summary_orders_clips_before_detecting_transitions():
    pytest.importorskip('mcp')
    source=Path(__file__).resolve().parents[1]/'tools/kdenlive-live-mcp'
    if not source.exists():pytest.skip('Optional live MCP checkout is absent')
    sys.path.insert(0,str(source))
    from types import SimpleNamespace
    from mcp_kdenlive.tools import timeline
    class Recorder:
        def __init__(self):self.functions={}
        def tool(self):
            def register(function):
                self.functions[function.__name__]=function
                return function
            return register
    class DBus:
        def get_all_tracks_info(self):return [{'id':4,'audio':False,'name':'V2'}]
        def get_clips_on_track(self,track):
            return [{'id':30,'position':300,'duration':744,'name':'video.mp4'},
                    {'id':10,'position':0,'duration':150,'name':'video.mp4'},
                    {'id':20,'position':150,'duration':150,'name':'video.mp4'}]
    helpers=SimpleNamespace(get_resolve=lambda ctx:SimpleNamespace(_dbus=DBus()),
                            get_fps=lambda ctx:30,format_tc=lambda frames,fps:str(frames))
    recorder=Recorder();timeline.register(recorder,helpers)
    text=recorder.functions['get_timeline_summary'](None)
    assert 'dissolve' not in text
    assert text.index('| 0 | 10 |')<text.index('| 1 | 20 |')<text.index('| 2 | 30 |')
