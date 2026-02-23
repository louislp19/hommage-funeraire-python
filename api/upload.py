import os
import json
import uuid
from http.server import BaseHTTPRequestHandler
import vercel_blob

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            token = os.environ["BLOB_READ_WRITE_TOKEN"]
            pathname = f"memorials/demo/{uuid.uuid4()}.jpg"
            
            # NO set_token - utilise env auto
            blob = vercel_blob.put(pathname, b"test image data", 
                                 token=token, access="public")
            
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
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
