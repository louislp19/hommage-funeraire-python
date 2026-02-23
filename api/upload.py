import os
import json
import uuid
from http.server import BaseHTTPRequestHandler
import vercel_blob

# Init Blob
vercel_blob.set_token(os.environ["BLOB_READ_WRITE_TOKEN"])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Upload TEST image vers Blob
            memorial_id = "demo"
            pathname = f"memorials/{memorial_id}/{uuid.uuid4()}.jpg"
            
            # 1KB test image
            test_image = b"/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8A..."  # base64 mini image
            
            blob = vercel_blob.put(pathname, test_image, access="public")
            
            response = {
                "success": True,
                "message": "BLOB UPLOAD OK",
                "url": blob["url"],
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
