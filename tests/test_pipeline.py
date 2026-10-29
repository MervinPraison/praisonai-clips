import json

from praisonai_shorts_studio import media
from praisonai_shorts_studio.pipeline import Pipeline, default_config
from praisonai_shorts_studio.preview import generate
from praisonai_shorts_studio.store import Store


class FixtureBackend:
    """Synthetic API fixtures; never used by production code or real-video output."""
    def __init__(self):
        self.calls = []
        self.review_frame_versions = set()

    def transcribe(self, audio):
        self.calls.append('transcribe')
        return {'text': 'One. Two. Three.', 'words': [
            {'word':'One','start':.3,'end':.8},
            {'word':'Two','start':1.4,'end':2.0},
            {'word':'Three','start':2.6,'end':3.2}]}

    def scenes(self, frames):
        self.calls.append('scenes')
        return {'scenes':[{'time':t, 'scene':'Test pattern','actions':'None',
            'screen_content':'Synthetic color test','visible_text':'','subjects':[],
            'confidence':1} for t,_ in frames]}

    def select(self, evidence):
        self.calls.append('select')
        option=evidence['validated_moment_options'][0]
        return {'clips':[{'option_id':option['option_id'], 'title':'<script>Fixture</script>',
                          'rationale':'Synthetic pipeline fixture','score':1}]}

    def crop(self, frames, evidence):
        self.calls.append('crop')
        return {'mode':'crop','center_x':.5,'center_y':.5,'confidence':1,'reason':'Synthetic fixture'}

    def review(self, frames, evidence):
        self.calls.append('review')
        self.review_frame_versions.add(frames[0][1].parent.name)
        if evidence['edl']['mode'] == 'crop':
            return {'accepted':False,'confidence':1,'defects':['Synthetic crop defect'],'repair':'fit'}
        return {'accepted':True,'confidence':1,'defects':[],'repair':'none'}


def test_end_to_end_render_repair_promote_and_resume(tmp_path):
    source=tmp_path/'input.mp4'
    media.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
        'testsrc2=size=320x180:rate=30:duration=4','-f','lavfi','-i',
        'sine=frequency=440:sample_rate=48000:duration=4','-c:v','libx264',
        '-threads','2','-preset','ultrafast','-c:a','aac',source])
    store=Store(tmp_path/'data')
    job=store.create(source,default_config(min_duration=1,max_duration=3,max_clips=1))
    backend=FixtureBackend()
    result=Pipeline(store,job,backend).run()
    assert store.get(job)['status']=='completed'
    assert len(result['accepted'])==1 and not result['drafts']
    from pathlib import Path
    clip=Path(result['accepted'][0]['path'])
    assert json.loads((clip/'edl.json').read_text())['mode']=='fit'
    assert json.loads((clip/'review.json').read_text())['attempt']==2
    assert not list((store.job_dir(job)/'drafts').iterdir())
    page=generate(store).read_text()
    assert '&lt;script&gt;Fixture&lt;/script&gt;' in page
    assert '<script>Fixture</script>' not in page
    assert 'accepted/clip-01/video.mp4' in page
    assert len(backend.review_frame_versions)==2  # repaired render must not reuse stale crop frames
    calls=list(backend.calls)
    assert Pipeline(store,job,backend).run()==result
    assert backend.calls==calls


def test_explicit_review_stages_resume_without_repeating_analysis(tmp_path):
    source = tmp_path / 'input.mp4'
    media.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
        'testsrc2=size=320x180:rate=30:duration=4','-f','lavfi','-i',
        'sine=frequency=440:sample_rate=48000:duration=4','-c:v','libx264',
        '-threads','2','-preset','ultrafast','-c:a','aac',source])
    store = Store(tmp_path/'data')
    job = store.create(source, default_config(min_duration=1,max_duration=3,max_clips=1))
    backend = FixtureBackend()
    evidence = Pipeline(store,job,backend).run(until='evidence')
    assert evidence['stage'] == 'evidence_ready'
    assert store.get(job)['status'] == 'paused'
    assert 'select' not in backend.calls and not (store.job_dir(job)/'manifest.json').exists()
    selection = Pipeline(store,job,backend).run(until='selection')
    assert selection['stage'] == 'selection_ready' and len(selection['selections']) == 1
    assert store.get(job)['status'] == 'paused' and 'crop' not in backend.calls
    before = list(backend.calls)
    result = Pipeline(store,job,backend).run()
    assert store.get(job)['status'] == 'completed' and len(result['accepted']) == 1
    assert backend.calls.count('transcribe') == before.count('transcribe')
    assert backend.calls.count('scenes') == before.count('scenes')
    assert backend.calls.count('select') == before.count('select')


def test_source_analysis_is_reused_across_jobs_but_not_models(tmp_path):
    source = tmp_path / 'landscape.mp4'
    media.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30:duration=6', '-f', 'lavfi', '-i',
        'sine=frequency=440:sample_rate=48000:duration=6', '-c:v', 'libx264',
        '-threads', '2', '-preset', 'ultrafast', '-c:a', 'aac', source])
    store = Store(tmp_path / 'data')
    backend = FixtureBackend()
    for maximum, vision_model in [(1, 'model-a'), (2, 'model-a'), (2, 'model-b')]:
        job = store.create(source, default_config(max_clips=maximum, vision_model=vision_model))
        assert Pipeline(store, job, backend).run(until='evidence')['scenes'] == 2
    assert backend.calls.count('transcribe') == 1
    assert backend.calls.count('scenes') == 2
    assert len(list((store.root / 'analysis-cache').glob('transcription-*.json'))) == 1


def test_zero_duration_provider_word_is_flagged_and_does_not_block_selection(tmp_path):
    source = tmp_path / 'input.mp4'
    media.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=320x180:rate=30:duration=4', '-f', 'lavfi', '-i',
        'sine=frequency=440:sample_rate=48000:duration=4', '-c:v', 'libx264',
        '-threads', '2', '-preset', 'ultrafast', '-c:a', 'aac', source])

    class ZeroBackend(FixtureBackend):
        def transcribe(self, audio):
            result = super().transcribe(audio)
            result['words'][1]['end'] = result['words'][1]['start']
            return result

    store = Store(tmp_path / 'data')
    job = store.create(source, default_config(min_duration=1, max_duration=3, max_clips=1))
    result = Pipeline(store, job, ZeroBackend()).run(until='selection')
    assert result['selections']
    transcript = json.loads((store.job_dir(job) / 'transcript.json').read_text())
    assert transcript['alignment_warnings'][0]['word'] == 'Two.'
    assert transcript['words'][1]['end'] > transcript['words'][1]['start']
