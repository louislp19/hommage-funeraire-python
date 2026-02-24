import json
from http.server import BaseHTTPRequestHandler
import vercel_blob


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            events = {}
            portraits = {}

            # List all memorial photos
            cursor = None
            while True:
                kwargs = {"prefix": "memorial/", "limit": 1000}
                if cursor:
                    kwargs["cursor"] = cursor
                result = vercel_blob.list(kwargs)
                for blob in result.get('blobs', []):
                    parts = blob.get('pathname', '').split('/')
                    if len(parts) >= 3:
                        slug = parts[1]
                        uploaded_at = blob.get('uploadedAt', '')
                        if slug not in events:
                            events[slug] = {'count': 0, 'latest': ''}
                        events[slug]['count'] += 1
                        if uploaded_at > events[slug]['latest']:
                            events[slug]['latest'] = uploaded_at
                cursor = result.get('cursor')
                if not result.get('hasMore') or not cursor:
                    break

            # List portrait photos
            cursor = None
            while True:
                kwargs = {"prefix": "portrait/", "limit": 1000}
                if cursor:
                    kwargs["cursor"] = cursor
                result = vercel_blob.list(kwargs)
                for blob in result.get('blobs', []):
                    pathname = blob.get('pathname', '')
                    # portrait/{slug}.ext
                    parts = pathname.split('/')
                    if len(parts) == 2:
                        slug = parts[1].rsplit('.', 1)[0]
                        portraits[slug] = blob.get('url', '')
                cursor = result.get('cursor')
                if not result.get('hasMore') or not cursor:
                    break

            event_list = [
                {
                    'slug': slug,
                    'count': data['count'],
                    'latest': data['latest'],
                    'portrait': portraits.get(slug, '')
                }
                for slug, data in events.items()
            ]
            event_list.sort(key=lambda x: x['latest'], reverse=True)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(event_list).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
