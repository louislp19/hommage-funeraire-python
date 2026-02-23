import os
import json
import time
from http.server import BaseHTTPRequestHandler
from vercel_blob import put

BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN")
if not BLOB_TOKEN:
    raise ValueError("BLOB_READ_WRITE_TOKEN manquant")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form (simplifié pour 1 fichier)
            boundary = self.headers['Content-Type'].split('boundary=')[1]
            
            # Extraire memorialId et file (logique simplifiée)
            memorial_id = "test"  # fixe pour POC
            
            # Simuler upload (version minimale)
            timestamp = int(time.time() * 1000)
            pathname = f"memorials/{memorial_id}/{timestamp}-test.jpg"
            
            # Upload vers Blob
            blob = put(
                pathname,
                b"fake image data for test",  # fichier test
                token=BLOB_TOKEN,
                access="public"
            )
            
            response = {
                "success": True,
                "message": "Upload test OK",
                "uploads": [{"url": blob["url"], "pathname": pathname}]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
