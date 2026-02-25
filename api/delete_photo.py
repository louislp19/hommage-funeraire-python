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
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            event = sanitize_event(body.get('event', ''))
            pin = str(body.get('pin', '')).strip()
            photo_url = body.get('url', '').strip()

            if not event or not pin or not photo_url:
                self._respond(400, {'success': False, 'error': 'Paramètres manquants'})
                return

            if f'memorial/{event}/' not in photo_url:
                self._respond(403, {'success': False, 'error': 'URL non autorisée'})
                return

            config = self._load_config(event)
            if config is None:
                self._respond(404, {'success': False, 'error': 'Mémorial non trouvé'})
                return
            if config.get('pin', '') != pin:
                self._respond(403, {'success': False, 'error': 'PIN incorrect'})
                return

            # Extract storage path from public URL
            path = photo_url.split(f'/storage/v1/object/public/{BUCKET}/')[1]
            sb = _sb()
            sb.storage.from_(BUCKET).remove([path])
            self._respond(200, {'success': True})

        except Exception as e:
            self._respond(500, {'success': False, 'error': str(e)})

    def _load_config(self, event):
        try:
            sb = _sb()
            data = sb.storage.from_(BUCKET).download(f'config/{event}.json')
            return json.loads(data)
        except Exception:
            return None

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
