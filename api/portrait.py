import os
import json
import re
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
                raise Exception("Paramètre event requis")

            portrait = None
            for key in form.keys():
                field = form[key]
                if hasattr(field, 'filename') and field.filename:
                    portrait = field
                    break

            if portrait is None:
                raise Exception("Aucune photo sélectionnée")

            file_bytes = portrait.file.read()
            if not file_bytes:
                raise Exception("Fichier vide")

            ext = 'jpg'
            if '.' in portrait.filename:
                ext = portrait.filename.rsplit('.', 1)[-1].lower()
            if ext not in ('jpg', 'jpeg', 'png', 'webp'):
                ext = 'jpg'

            path = f"portrait/{event}.{ext}"

            sb = _sb()
            sb.storage.from_(BUCKET).upload(
                path,
                file_bytes,
                file_options={"content-type": portrait.type or "image/jpeg", "upsert": "true"}
            )
            url = sb.storage.from_(BUCKET).get_public_url(path)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "url": url}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
