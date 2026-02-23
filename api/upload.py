import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid
import hashlib
import time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'})
            
            list_key = "GLOBAL_MEMORIAL_IMAGES"
            
            # Load URLs
            try:
                existing_data = vercel_blob.get(list_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_count = 0
            
            # Multi-files
            for key in form.keys():
                file_item = form[key]
                if file_item.filename:
                    # Nom 100% unique : uuid + hash + time
                    file_bytes = file_item.file.read()
                    content_hash = hashlib.md5(file_bytes).hexdigest()[:8]
                    pathname = f"memorial/{uuid.uuid4().hex}-{content_hash}-{int(time.time())}.{file_item.filename.rsplit('.', 1)[-1] if '.' in file_item.filename else 'jpg'}"
                    
                    # PUT avec allowOverwrite TRUE (boolean !)
                    blob = vercel_blob.put(
                        pathname,
                        file_bytes,
                        {
                            "access": "public",
                            "allowOverwrite": True,  # BOOLEAN true → KILLS 400 error [page:1]
                            "addRandomSuffix": True,  # DOUBLE safe
                            "contentType": file_item.type or "image/jpeg"
                        }
                    )
                    if blob.get('url') not in urls:
                        urls.append(blob['url'])
                        new_count += 1
            
            # Save LIST avec access public explicite
            vercel_blob.put(
                list_key,
                json.dumps(urls).encode('utf-8'),
                {
                    "access": "public"  # FIX slideshow fetch !
                }
            )
            
            response = {
                "success": True,
                "new_count": new_count,
                "total_count": len(urls),
                "last_url": urls[-1] if urls else None,
                "debug_pathname": pathname
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

def main():
    handler().do_POST()

if __name__ == "__main__":
    main()
