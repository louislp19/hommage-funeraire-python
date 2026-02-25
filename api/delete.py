import os
import json
import re
from http.server import BaseHTTPRequestHandler
from supabase import create_client

BUCKET = 'hommage'


def _sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


def sanitize_event(event):
    return re.sub(r'[^a-zA-Z0-9\-_]', '', event)[:50]


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            event = sanitize_event(data.get('event', ''))
            if not event:
                raise Exception("Paramètre event requis")

            sb = _sb()
            paths_to_delete = []

            # Collect memorial photos
            folder = f"memorial/{event}"
            offset = 0
            limit = 1000
            while True:
                items = sb.storage.from_(BUCKET).list(folder, {'limit': limit, 'offset': offset})
                if not items:
                    break
                for f in items:
                    if f.get('id') is not None:
                        paths_to_delete.append(f"{folder}/{f['name']}")
                if len(items) < limit:
                    break
                offset += limit

            # Collect portrait
            portrait_items = sb.storage.from_(BUCKET).list('portrait', {'limit': 100})
            for f in portrait_items:
                if f.get('id') is not None and f['name'].startswith(f'{event}.'):
                    paths_to_delete.append(f"portrait/{f['name']}")

            # Collect config
            try:
                sb.storage.from_(BUCKET).download(f'config/{event}.json')
                paths_to_delete.append(f'config/{event}.json')
            except Exception:
                pass

            if paths_to_delete:
                sb.storage.from_(BUCKET).remove(paths_to_delete)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "deleted": len(paths_to_delete)
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode('utf-8'))
