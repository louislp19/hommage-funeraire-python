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
            
            memorial_key = "GLOBAL_MEMORIAL_JSON"
            
            # Load URLs existantes
            try:
                existing_data = vercel_blob.get(memorial_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_urls = []
            
            # Multi files
            for key in form.keys():
                file_item = form[key]
                if hasattr(file_item, 'file') and file_item.file:
                    image_data = file_item.file.read()
                    # UUID unique = NO duplicate
                    pathname = f"memorials/global/{uuid.uuid4()}.jpg"
                    blob = vercel_blob.put(pathname, image_data)
                    new_urls.append(blob["url"])
            
            # Append
            urls.extend(new_urls)
            vercel_blob.put(memorial_key, json.dumps(urls).encode())
            
            response = {
                "success": True,
                "new_count": len(new_urls),
                "total_count": len(urls),
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
