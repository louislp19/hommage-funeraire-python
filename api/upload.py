import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid
import json as json_lib

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'})
            
            # ID mémorial unique
            memorial_id = form.getvalue('name', 'default').replace(' ', '_')
            
            # Charge images existantes
            existing_file = f"memorials/{memorial_id}.json"
            try:
                existing = json_lib.loads(vercel_blob.get(existing_file).decode())
            except:
                existing = []
            
            new_urls = []
            
            # TOUS les files (multiples)
            for key in form.keys():
                if key.startswith('files') or key == 'file':
                    file_item = form[key]
                    if hasattr(file_item, 'file') and file_item.file:
                        data = file_item.file.read()
                        pathname = f"memorials/{memorial_id}/{uuid.uuid4()}-{getattr(file_item, 'filename', 'image.jpg')}"
                        blob = vercel_blob.put(pathname, data)
                        new_urls.append(blob["url"])
            
            # Append + save
            all_urls = existing + new_urls
            vercel_blob.put(existing_file, json_lib.dumps(all_urls).encode())
            
            response = {
                "success": True,
                "new_count": len(new_urls),
                "total_count": len(all_urls),
                "memorial_id": memorial_id,
                "all_urls": all_urls
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
