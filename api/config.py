import os
import json
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from supabase import create_client

BUCKET = 'hommage'


def _sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


def sanitize_event(event):
    return re.sub(r'[^a-zA-Z0-9\-_]', '', event)[:50]


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        event = sanitize_event(query.get('event', [''])[0])
        pin = query.get('pin', [''])[0].strip()

        if not event or not pin:
            self._respond(400, {'success': False, 'error': 'Paramètres manquants'})
            return

        config = self._load_config(event)
        if config is None:
            self._respond(404, {'success': False, 'error': 'Mémorial non trouvé'})
            return
        if config.get('pin', '') != pin:
            self._respond(403, {'success': False, 'error': 'PIN incorrect'})
            return

        self._respond(200, {'success': True, 'duration': config.get('duration', '5')})

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            event = sanitize_event(body.get('event', ''))
            pin = str(body.get('pin', '')).strip()
            action = body.get('action', '')

            if action == 'set_expiry':
                if not event:
                    self._respond(400, {'success': False, 'error': 'Paramètre event requis'})
                    return
                expiry_date = str(body.get('expiry_date', '')).strip()
                config = self._load_config(event) or {}
                if expiry_date:
                    config['expiry_date'] = expiry_date
                else:
                    config.pop('expiry_date', None)
                self._save_config(event, config)
                self._respond(200, {'success': True})
                return

            if not event or not pin:
                self._respond(400, {'success': False, 'error': 'Paramètres manquants'})
                return

            if action == 'save':
                duration = str(body.get('duration', '5'))
                self._save_config(event, {'pin': pin, 'duration': duration})
                self._respond(200, {'success': True})

            elif action == 'update_duration':
                config = self._load_config(event)
                if config is None:
                    self._respond(404, {'success': False, 'error': 'Mémorial non trouvé'})
                    return
                if config.get('pin', '') != pin:
                    self._respond(403, {'success': False, 'error': 'PIN incorrect'})
                    return
                config['duration'] = str(body.get('duration', config.get('duration', '5')))
                self._save_config(event, config)
                self._respond(200, {'success': True})

            else:
                self._respond(400, {'success': False, 'error': 'Action inconnue'})

        except Exception as e:
            self._respond(500, {'success': False, 'error': str(e)})

    def _load_config(self, event):
        try:
            sb = _sb()
            data = sb.storage.from_(BUCKET).download(f'config/{event}.json')
            return json.loads(data)
        except Exception:
            return None

    def _save_config(self, event, config):
        sb = _sb()
        sb.storage.from_(BUCKET).upload(
            f'config/{event}.json',
            json.dumps(config).encode('utf-8'),
            file_options={'content-type': 'application/json', 'upsert': 'true'}
        )

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
