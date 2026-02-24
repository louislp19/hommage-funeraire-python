import json
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import vercel_blob


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

            prefix = f"memorial/{event}/"
            all_blobs = []
            cursor = None

            # Fetch all pages
            while True:
                options = {"prefix": prefix, "limit": 1000}
                if cursor:
                    options["cursor"] = cursor

                result = vercel_blob.list(options)
                blobs = result.get('blobs', [])
                all_blobs.extend(blobs)

                if not result.get('hasMore'):
                    break
                cursor = result.get('cursor')

            # Sort by upload date (oldest first) so slideshow shows in order
            all_blobs.sort(key=lambda b: b.get('uploadedAt', ''))
            urls = [b['url'] for b in all_blobs if b.get('url')]

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
