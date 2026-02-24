import json
import re
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob


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

            # Find the portrait file among all form fields
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

            # Stored at a fixed path so it can be overwritten
            pathname = f"portrait/{event}.{ext}"

            blob = vercel_blob.put(
                pathname,
                file_bytes,
                {
                    "access": "public",
                    "allowOverwrite": True,
                    "addRandomSuffix": False,
                    "contentType": portrait.type or "image/jpeg"
                }
            )

            url = blob.get('url') or blob.get('downloadUrl', '')

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
