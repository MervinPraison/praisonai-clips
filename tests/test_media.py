"""Real FFmpeg integration; the transcript below is explicitly a synthetic test fixture."""
import json
import shutil
import subprocess

import pytest

from praisonai_shorts_studio import captions, media
from praisonai_shorts_studio.models import EDL, Mapping, Word

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg'), reason='FFmpeg not installed')


@pytest.fixture
def source(tmp_path):
    path = tmp_path/'source.mp4'
    media.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
               'testsrc2=size=640x360:rate=30:duration=4','-f','lavfi','-i',
               'sine=frequency=440:sample_rate=48000:duration=4','-c:v','libx264',
               '-threads','2','-preset','ultrafast','-c:a','aac',path])
    return path


@pytest.mark.parametrize('mode', ['fit','crop'])
def test_real_render_captions_and_decode(source, tmp_path, mode):
    edl = EDL(title='Synthetic test', rationale='Render regression fixture', mode=mode,
              mappings=[Mapping(source_start=1,source_end=3,output_start=0)])
    words = [Word(word='Synthetic', start=1.1,end=1.7), Word(word='test.',start=1.8,end=2.5)]
    captions.export(tmp_path, words, edl)
    video = media.render(source,tmp_path,edl,lambda:None)
    assert media.technical_review(video,2,lambda:None) == []
    assert (tmp_path/'words.json').exists()
    frame = media.frame(video,tmp_path/'caption-frame.jpg',1)
    assert frame.stat().st_size > 1000


def test_normalize_preserves_common_offset_and_audio_delay(tmp_path):
    source = tmp_path/'offset.mkv'
    # Picture begins at PTS 5.0, sound at 5.5. Canonical audio must retain the 0.5s gap.
    media.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
               'color=red:size=320x180:rate=30:duration=2', '-f','lavfi','-i',
               'sine=frequency=1000:sample_rate=48000:duration=1.5',
               '-vf','setpts=PTS+5/TB','-af','asetpts=PTS+5.5/TB',
               '-c:v','libx264','-threads','2','-c:a','pcm_s16le',source])
    meta=media.probe(source)
    assert meta['start_time'] == pytest.approx(5, abs=.05)
    target=tmp_path/'canonical.mp4'
    media.normalize(source,target,meta,lambda:None)
    import array
    result=subprocess.run(['ffmpeg','-v','error','-i',str(target),'-map','0:a:0',
                           '-f','f32le','-ac','1','-ar','48000','-'],capture_output=True,check=True)
    samples=array.array('f', result.stdout)
    assert max(abs(v) for v in samples[:int(.35*48000)]) < .005
    assert max(abs(v) for v in samples[int(.65*48000):int(.9*48000)]) > .05
