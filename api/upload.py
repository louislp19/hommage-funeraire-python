import os
import json
import re
import uuid
import hashlib
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
from supabase import create_client

BUCKET = 'hommage'


def _sb():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])


def sanitize_event(event):
    return re.sub(r'[^a-zA-Z0-9\-_]', '', event)[:50]


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length)
            }
            form = FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)

            event = sanitize_event(form.getvalue('event', ''))
            if not event:
                event = 'default'

            sb = _sb()
            prefix = f"memorial/{event}"
            uploaded_urls = []

            items = []
            for key in form.keys():
                field = form[key]
                if isinstance(field, list):
                    items.extend(field)
                else:
                    items.append(field)

            for item in items:
                if not hasattr(item, 'filename') or not item.filename:
                    continue

                file_bytes = item.file.read()
                if not file_bytes:
                    continue

                ext = 'jpg'
                if '.' in item.filename:
                    ext = item.filename.rsplit('.', 1)[-1].lower()
                if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'):
                    ext = 'jpg'

                content_hash = hashlib.md5(file_bytes).hexdigest()[:8]
                path = f"{prefix}/{uuid.uuid4().hex}-{content_hash}.{ext}"

                sb.storage.from_(BUCKET).upload(
                    path,
                    file_bytes,
                    file_options={"content-type": item.type or "image/jpeg", "upsert": "true"}
                )
                url = sb.storage.from_(BUCKET).get_public_url(path)
                if url:
                    uploaded_urls.append(url)

            if len(uploaded_urls) == 0:
                raise Exception("Aucun fichier valide reçu. Vérifiez que les photos sont bien sélectionnées.")

            response = {
                "success": True,
                "event": event,
                "new_count": len(uploaded_urls),
                "urls": uploaded_urls
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
