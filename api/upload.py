import os
import json
import time
from http.server import BaseHTTPRequestHandler
import vercel_blob
from cgi import parse_multipart

# Config Blob
os.environ["BLOB_READ_WRITE_TOKEN"] = os.getenv("BLOB_READ_WRITE_TOKEN", "")
vercel_blob.set_token(os.environ["BLOB_READ_WRITE_TOKEN"])

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers['Content-Type']
            
            # Parse multipart
            environ = {
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': str(content_length),
            }
            form = parse_multipart(environ, self.rfile.read(content_length))
            
            uploads = []
            memorial_id = form.get('memorial_id', ['test'])[0]
            
            # Traiter fichiers
            files = form.get('files', [])
            for file_data in files:
                if file_data:
                    filename = file_data.filename
                    file_content = file_data.file.read()
                    
                    pathname = f"memorials/{memorial_id}/{int(time.time()*1000)}-{filename}"
                    
                    blob = vercel_blob.put(
                        pathname,
                        file_content,
                        access="public"
                    )
                    
                    uploads.append({
                        "url": blob["url"],
                        "pathname": blob["pathname"],
                        "name": filename
                    })
            
            response = {
                "success": True,
                "message": f"{len(uploads)} fichier(s) uploadé(s)",
                "uploads": uploads
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
