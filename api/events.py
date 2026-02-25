import os
import json
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
from supabase import create_client

BUCKET = 'hommage'


def _sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            sb = _sb()
            events = {}
            portraits = {}

            # List all event folders under memorial/
            event_folders = sb.storage.from_(BUCKET).list('memorial', {'limit': 1000})
            for folder in event_folders:
                if folder.get('id') is not None:
                    continue  # skip files, only process folders
                slug = folder['name']
                photos = sb.storage.from_(BUCKET).list(f'memorial/{slug}', {
                    'limit': 1000,
                    'sortBy': {'column': 'created_at', 'order': 'desc'}
                })
                photo_files = [f for f in photos if f.get('id') is not None]
                if photo_files:
                    events[slug] = {
                        'count': len(photo_files),
                        'latest': photo_files[0].get('created_at', '')
                    }

            # List portraits
            portrait_items = sb.storage.from_(BUCKET).list('portrait', {'limit': 1000})
            for f in portrait_items:
                if f.get('id') is not None:
                    slug = f['name'].rsplit('.', 1)[0]
                    portraits[slug] = sb.storage.from_(BUCKET).get_public_url(f"portrait/{f['name']}")

            # Fetch configs
            configs = {}
            config_items = sb.storage.from_(BUCKET).list('config', {'limit': 1000})
            config_slugs = [
                f['name'].rsplit('.', 1)[0]
                for f in config_items
                if f.get('id') is not None and f['name'].endswith('.json')
                and f['name'].rsplit('.', 1)[0] in events
            ]

            def fetch_config(slug):
                try:
                    _sb_local = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
                    data = _sb_local.storage.from_(BUCKET).download(f'config/{slug}.json')
                    return json.loads(data)
                except Exception:
                    return {}

            if config_slugs:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(fetch_config, slug): slug for slug in config_slugs}
                    for future, slug in futures.items():
                        configs[slug] = future.result()

            event_list = [
                {
                    'slug': slug,
                    'count': data['count'],
                    'latest': data['latest'],
                    'portrait': portraits.get(slug, ''),
                    'expiry': configs.get(slug, {}).get('expiry_date', ''),
                    'duration': configs.get(slug, {}).get('duration', '5'),
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
