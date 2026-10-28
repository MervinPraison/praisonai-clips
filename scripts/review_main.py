"""Re-review uncertain main-video edits against original source reference frames."""
import fcntl
import json
from pathlib import Path

from dotenv import load_dotenv
from praisonai_shorts_studio.ai import OpenAIBackend
from praisonai_shorts_studio.models import EDL
from praisonai_shorts_studio.pipeline import Pipeline
from praisonai_shorts_studio.preview import generate
from praisonai_shorts_studio.review import inspect_render
from praisonai_shorts_studio.store import Store, write_json

load_dotenv()
store=Store('data')
job_id=Path('data/main-job.txt').read_text().strip()
pipeline=Pipeline(store,job_id)
backend=OpenAIBackend('gpt-4o-mini','gpt-4o-mini','whisper-1')
with (pipeline.folder/'worker.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    store.update(job_id,status='running',stage='review-with-source-reference')
    manifest=json.loads((pipeline.folder/'manifest.json').read_text())
    remaining=[]
    try:
        for entry in manifest['drafts']:
            folder=Path(entry['path'])
            edl=EDL.model_validate_json((folder/'edl.json').read_text())
            mapped=json.loads((folder/'words.json').read_text())
            def cache(name, inputs, compute):
                return pipeline.cache(folder.name+'-'+name,inputs,compute)
            report=inspect_render(pipeline.folder/'source.mp4',folder/'video.mp4',folder,edl,mapped,backend,cache,pipeline.check)
            report['attempt']=2
            write_json(folder/'review-attempt-2.json',report)
            write_json(folder/'review.json',report)
            entry['review']=report
            if report['accepted']:
                destination=pipeline.folder/'accepted'/folder.name
                destination.parent.mkdir(exist_ok=True)
                folder.rename(destination)
                entry['path']=str(destination)
                manifest['accepted'].append(entry)
            else:
                remaining.append(entry)
            print(entry['title'], 'ACCEPTED' if report['accepted'] else 'DRAFT',flush=True)
        manifest['drafts']=remaining
        write_json(pipeline.folder/'manifest.json',manifest)
        store.update(job_id,status='completed',stage='complete')
        generate(store)
    except Exception as exc:
        store.update(job_id,status='failed',error=str(exc)[:1000])
        raise
