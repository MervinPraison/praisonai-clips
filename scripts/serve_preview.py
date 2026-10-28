"""Serve the local preview and keep job state fresh. Bind only to localhost."""
import os
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv
from praisonai_shorts_studio.preview import generate
from praisonai_shorts_studio.store import Store

load_dotenv()
store = Store(os.getenv('SHORTS_DATA_DIR', 'data'))
generate(store)

class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(store.root), **kwargs)

    def do_GET(self):
        if self.path.split('?')[0] in ['/', '/preview/', '/preview/index.html']:
            generate(store)
            self.path = '/preview/index.html'
        super().do_GET()

print('Preview: http://127.0.0.1:8765/preview/index.html', flush=True)
ThreadingHTTPServer(('127.0.0.1', 8765), PreviewHandler).serve_forever()
