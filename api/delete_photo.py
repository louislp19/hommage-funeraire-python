import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler
import vercel_blob


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

            # Verify the URL belongs to this event before checking PIN
            if f'memorial/{event}/' not in photo_url:
                self._respond(403, {'success': False, 'error': 'URL non autorisée'})
                return

            # Verify PIN
            config = self._load_config(event)
            if config is None:
                self._respond(404, {'success': False, 'error': 'Mémorial non trouvé'})
                return
            if config.get('pin', '') != pin:
                self._respond(403, {'success': False, 'error': 'PIN incorrect'})
                return

            vercel_blob.delete([photo_url])
            self._respond(200, {'success': True})

        except Exception as e:
            self._respond(500, {'success': False, 'error': str(e)})

    def _load_config(self, event):
        try:
            result = vercel_blob.list({'prefix': f'config/{event}.json', 'limit': 1})
            blobs = result.get('blobs', [])
            if not blobs:
                return None
            url = blobs[0].get('url', '')
            if not url:
                return None
            with urllib.request.urlopen(url) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
