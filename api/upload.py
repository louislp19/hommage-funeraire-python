import os
import json
import uuid
from http.server import BaseHTTPRequestHandler
import vercel_blob

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            pathname = f"memorials/demo/{uuid.uuid4()}.jpg"
            
            # Syntaxe MINIMALE vercel_blob
            blob = vercel_blob.put(pathname, b"test image")
            
            response = {
                "success": True,
                "blob_url": blob["url"],
                "pathname": blob["pathname"]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            
        except Exception as e:
            response = {"error": str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
