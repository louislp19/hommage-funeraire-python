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
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            event = sanitize_event(params.get('event', [''])[0])

            if not event:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Parametre event requis"}).encode('utf-8'))
                return

            sb = _sb()
            folder = f"memorial/{event}"

            all_files = []
            offset = 0
            limit = 1000
            while True:
                items = sb.storage.from_(BUCKET).list(folder, {
                    'limit': limit,
                    'offset': offset,
                    'sortBy': {'column': 'created_at', 'order': 'asc'}
                })
                if not items:
                    break
                files = [f for f in items if f.get('id') is not None]
                all_files.extend(files)
                if len(items) < limit:
                    break
                offset += limit

            urls = [
                sb.storage.from_(BUCKET).get_public_url(f"{folder}/{f['name']}")
                for f in all_files
            ]

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(urls).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
