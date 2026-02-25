import os
import json
from datetime import date
from http.server import BaseHTTPRequestHandler
from supabase import create_client

BUCKET = 'hommage'


def _sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Called daily by Vercel Cron. Deletes memorials past their expiry date."""
        try:
            today = date.today().isoformat()
            deleted = []
            sb = _sb()

            # List all config files
            config_items = sb.storage.from_(BUCKET).list('config', {'limit': 1000})
            config_slugs = [
                f['name'].rsplit('.', 1)[0]
                for f in config_items
                if f.get('id') is not None and f['name'].endswith('.json')
            ]

            for slug in config_slugs:
                try:
                    data = sb.storage.from_(BUCKET).download(f'config/{slug}.json')
                    config = json.loads(data)
                except Exception:
                    continue

                expiry = config.get('expiry_date', '')
                if not expiry or expiry > today:
                    continue

                paths_to_delete = [f'config/{slug}.json']

                # Collect memorial photos
                folder = f'memorial/{slug}'
                offset = 0
                limit = 1000
                while True:
                    items = sb.storage.from_(BUCKET).list(folder, {'limit': limit, 'offset': offset})
                    if not items:
                        break
                    for f in items:
                        if f.get('id') is not None:
                            paths_to_delete.append(f"{folder}/{f['name']}")
                    if len(items) < limit:
                        break
                    offset += limit

                # Collect portrait
                portrait_items = sb.storage.from_(BUCKET).list('portrait', {'limit': 100})
                for f in portrait_items:
                    if f.get('id') is not None and f['name'].startswith(f'{slug}.'):
                        paths_to_delete.append(f"portrait/{f['name']}")

                if paths_to_delete:
                    sb.storage.from_(BUCKET).remove(paths_to_delete)
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
