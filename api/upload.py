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
            
            # Default memorial
            memorial_key = "GLOBAL_MEMORIAL"
            
            # Load existing
            try:
                existing_data = vercel_blob.get(memorial_key).decode()
                urls = json.loads(existing_data)
            except:
                urls = []
            
            # New files
            new_urls = []
            for key in form.keys():
                file_item = form[key]
                if hasattr(file_item, 'file') and file_item.file:
                    data = file_item.file.read()
                    pathname = f"memorials/global/{uuid.uuid4()}.jpg"
                    blob = vercel_blob.put(pathname, data)
                    new_urls.append(blob["url"])
            
            # Append & save
            urls.extend(new_urls)
            vercel_blob.put(memorial_key, json.dumps(urls).encode())
            
            response = {
                "success": True,
                "new": len(new_urls),
                "total": len(urls),
                "urls": urls
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
