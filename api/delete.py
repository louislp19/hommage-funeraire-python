import json
import re
from http.server import BaseHTTPRequestHandler
import vercel_blob


def sanitize_event(event):
    return re.sub(r'[^a-zA-Z0-9\-_]', '', event)[:50]


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            event = sanitize_event(data.get('event', ''))
            if not event:
                raise Exception("Paramètre event requis")

            urls_to_delete = []

            # Collect memorial photos
            cursor = None
            while True:
                kwargs = {"prefix": f"memorial/{event}/", "limit": 1000}
                if cursor:
                    kwargs["cursor"] = cursor
                result = vercel_blob.list(kwargs)
                for blob in result.get('blobs', []):
                    url = blob.get('url', '')
                    if url:
                        urls_to_delete.append(url)
                cursor = result.get('cursor')
                if not result.get('hasMore') or not cursor:
                    break

            # Collect portrait
            cursor = None
            while True:
                kwargs = {"prefix": f"portrait/{event}", "limit": 100}
                if cursor:
                    kwargs["cursor"] = cursor
                result = vercel_blob.list(kwargs)
                for blob in result.get('blobs', []):
                    url = blob.get('url', '')
                    if url:
                        urls_to_delete.append(url)
                cursor = result.get('cursor')
                if not result.get('hasMore') or not cursor:
                    break

            if urls_to_delete:
                vercel_blob.delete(urls_to_delete)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "deleted": len(urls_to_delete)
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode('utf-8'))
