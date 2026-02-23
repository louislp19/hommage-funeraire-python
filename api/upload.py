import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(fp=self.rfile, headers=self.headers)
            
            # Global memorial
            memorial_key = "GLOBAL_MEMORIAL_JSON"
            
            # Load existing URLs
            try:
                existing_data = vercel_blob.get(memorial_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_count = 0
            
            # All files
            for key in list(form.keys()):
                file_item = form[key]
                if hasattr(file_item, 'file') and file_item.file:
                    image_data = file_item.file.read()
                    pathname = f"memorials/global/{uuid.uuid4()}.jpg"
                    blob = vercel_blob.put(pathname, image_data)
                    urls.append(blob["url"])
                    new_count += 1
            
            # Save updated list
            vercel_blob.put(memorial_key, json.dumps(urls).encode())
            
            response = {
                "success": True,
                "new_count": new_count,
                "total_count": len(urls),
                "urls": urls[-5:]  # last 5 for preview
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            response = {"error": str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
