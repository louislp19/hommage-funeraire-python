import json
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler
import vercel_blob


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Called daily by Vercel Cron. Deletes memorials past their expiry date."""
        try:
            today = date.today().isoformat()  # YYYY-MM-DD
            deleted = []

            # List all config files
            config_blobs = []
            cursor = None
            while True:
                kwargs = {"prefix": "config/", "limit": 1000}
                if cursor:
                    kwargs["cursor"] = cursor
                result = vercel_blob.list(kwargs)
                for blob in result.get('blobs', []):
                    parts = blob.get('pathname', '').split('/')
                    if len(parts) == 2:
                        slug = parts[1].rsplit('.', 1)[0]
                        config_blobs.append({'slug': slug, 'url': blob.get('url', '')})
                cursor = result.get('cursor')
                if not result.get('hasMore') or not cursor:
                    break

            for item in config_blobs:
                slug = item['slug']
                try:
                    with urllib.request.urlopen(item['url'], timeout=5) as resp:
                        config = json.loads(resp.read().decode('utf-8'))
                except Exception:
                    continue

                expiry = config.get('expiry_date', '')
                if not expiry or expiry > today:
                    continue

                # Collect all blobs to delete for this event
                urls_to_delete = [item['url']]  # config file itself

                for prefix in [f'memorial/{slug}/', f'portrait/{slug}']:
                    cursor2 = None
                    while True:
                        kw = {"prefix": prefix, "limit": 1000}
                        if cursor2:
                            kw["cursor"] = cursor2
                        r = vercel_blob.list(kw)
                        for b in r.get('blobs', []):
                            u = b.get('url', '')
                            if u:
                                urls_to_delete.append(u)
                        cursor2 = r.get('cursor')
                        if not r.get('hasMore') or not cursor2:
                            break

                if urls_to_delete:
                    vercel_blob.delete(urls_to_delete)
                    deleted.append(slug)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'date_checked': today,
                'deleted': deleted
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
