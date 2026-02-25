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

        if not event:
            self._respond(400, {'success': False, 'error': 'Paramètre event requis'})
            return

        try:
            sb = _sb()
            data = sb.storage.from_(BUCKET).download(f'config/{event}.json')
            config = json.loads(data)
            self._respond(200, {'success': True, 'pin': config.get('pin', '')})
        except Exception:
            self._respond(404, {'success': False, 'pin': ''})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
