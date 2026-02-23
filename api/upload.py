import os
import json
import uuid
from http.server import BaseHTTPRequestHandler
import vercel_blob

vercel_blob.set_token(os.environ["BLOB_READ_WRITE_TOKEN"])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Réponse IMMÉDIATE sans parsing fichier
            memorial_id = "demo"
            pathname = f"memorials/{memorial_id}/{uuid.uuid4()}.jpg"
            
            # Upload fichier TEST 1KB vers Blob
            test_data = b"demo image " * 100
            blob = vercel_blob.put(pathname, test_data, access="public")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "url": blob["url"],
                "message": "Blob OK - prêt pour vrais fichiers"
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
