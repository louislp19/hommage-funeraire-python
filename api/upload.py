import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'})
            
            urls = []
            memorial_name = form.getvalue('name', 'Unknown')
            
            # Multi files
            file_keys = [k for k in form.keys() if k.startswith('files')]
            for key in file_keys:
                file_item = form[key]
                if hasattr(file_item, 'file') and file_item.file:
                    data = file_item.file.read()
                    pathname = f"memorials/{memorial_name.replace(' ', '_')}/{uuid.uuid4()}-{file_item.filename}"
                    blob = vercel_blob.put(pathname, data)
                    urls.append(blob["url"])
            
            response = {
                "success": True,
                "urls": urls,
                "memorial": memorial_name.replace(' ', '_'),
                "count": len(urls)
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
