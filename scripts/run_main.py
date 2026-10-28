"""Wait for the user's main upload, then run paid transcription and the pipeline."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dotenv import load_dotenv
from praisonai_shorts_studio.media import probe
from praisonai_shorts_studio.pipeline import Pipeline, default_config
from praisonai_shorts_studio.store import Store

root = Path(__file__).resolve().parents[1]
load_dotenv(root / '.env')
source = root / 'input' / 'main video.mp4'
store = Store(root / 'data')
print('Waiting for main video to finish copying...', flush=True)
last_size = None
stable = 0
for attempt in range(180):
    size = source.stat().st_size if source.exists() else None
    stable = stable + 1 if size == last_size else 0
    last_size = size
    try:
        metadata = probe(source)
        if stable >= 2:
            break
    except (ValueError, FileNotFoundError):
        pass
    time.sleep(5)
else:
    raise SystemExit('Main video not readable after 15 minutes; resume once copying completes.')
print('Source ready: ' + json.dumps({k: metadata[k] for k in ['duration', 'width', 'height']}), flush=True)
if not os.getenv('OPENAI_API_KEY'):
    raise SystemExit('OPENAI_API_KEY is missing')
existing = [j for j in store.list() if j['source'] == str(source) and j['status'] != 'completed']
if existing:
    job_id = existing[0]['id']
else:
    job_id = store.create(source, default_config(vision_model='gpt-4o-mini', editor_model='gpt-4o-mini'))
(root / 'data' / 'main-job.txt').write_text(job_id)
print('Job: ' + job_id, flush=True)
try:
    result = Pipeline(store, job_id).run()
    print(json.dumps(result, indent=2), flush=True)
except Exception as exc:
    # SDK errors should not dump request headers or keys.
    print(type(exc).__name__ + ': ' + str(exc)[:1000], flush=True)
    raise SystemExit(1)
