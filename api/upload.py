import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            file_item = form['file']
            if not file_item.file:
                raise Exception("Pas de fichier")
            
            # VRAIS bytes image
            image_data = file_item.file.read()
            memorial_id = form.getvalue('memorialId', 'demo')
            pathname = f"memorials/{memorial_id}/{file_item.filename}"
            
            blob = vercel_blob.put(pathname, image_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "url": blob["url"],
                "filename": file_item.filename
            }).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
