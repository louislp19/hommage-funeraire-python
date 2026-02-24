import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import vercel_blob


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
            result = vercel_blob.list({'prefix': f'config/{event}.json', 'limit': 1})
            blobs = result.get('blobs', [])
            if not blobs:
                self._respond(404, {'success': False, 'pin': ''})
                return
            url = blobs[0].get('url', '')
            with urllib.request.urlopen(url) as resp:
                config = json.loads(resp.read().decode('utf-8'))
            self._respond(200, {'success': True, 'pin': config.get('pin', '')})
        except Exception as e:
            self._respond(500, {'success': False, 'error': str(e)})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
