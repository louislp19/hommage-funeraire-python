import json
import os
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        branding = {
            'salon_name': os.environ.get('SALON_NAME', ''),
            'logo_url':   os.environ.get('SALON_LOGO', ''),
            'color':      os.environ.get('SALON_COLOR', '#c9a84c'),
        }
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=300')
        self.end_headers()
        self.wfile.write(json.dumps(branding).encode('utf-8'))
