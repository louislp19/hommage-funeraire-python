import os
import json
import time
from http.server import BaseHTTPRequestHandler
import vercel_blob

# Config Blob
vercel_blob.set_token(os.environ["BLOB_READ_WRITE_TOKEN"])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            ctype = self.headers['Content-Type']
            
            if 'multipart/form-data' not in ctype:
                self._json_error("Format multipart requis", 400)
                return
            
            # Parse simple (1 fichier pour commencer)
            memorial_id = "test"  # fixe pour POC
            
            # Simuler fichier (version ultra simple)
            timestamp = int(time.time() * 1000)
            pathname = f"memorials/{memorial_id}/{timestamp}-test.jpg"
            
            # Upload vers Blob
            blob = vercel_blob.put(
                pathname,
                b"fake image data",  # bytes du fichier (à parser multipart plus tard)
                access="public"
            )
            
            response = {
                "success": True,
                "message": "Upload Blob OK",
                "url": blob["url"],
                "pathname": blob["pathname"]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            
        except Exception as e:
            self._json_error(f"Erreur Blob: {str(e)}", 500)

    def _json_error(self, message, status=500):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))
