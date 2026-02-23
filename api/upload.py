import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid
import time  # timestamp extra

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(
                fp=self.rfile, 
                headers=self.headers, 
                environ={'REQUEST_METHOD':'POST'}
            )
            
            list_key = "GLOBAL_MEMORIAL_IMAGES"
            
            # Load
            try:
                existing_data = vercel_blob.get(list_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_count = 0
            
            # Multi files
            for key in form.keys():
                file_item = form[key]
                if file_item.filename:
                    # UUID + timestamp + nom → 100% unique
                    timestamp = str(int(time.time()))
                    safe_filename = "".join(c for c in file_item.filename if c.isalnum() or c in ".-_ ")
                    pathname = f"memorial/{uuid.uuid4().hex}-{timestamp}-{safe_filename}"
                    
                    file_bytes = file_item.file.read()
                    
                    blob = vercel_blob.put(
                        pathname,
                        file_bytes,
                        {
                            "access": "public",
                            "addRandomSuffix": "true",  # STR "true" comme docs !
                            "contentType": file_item.type or "image/jpeg"
                        }
                    )
                    urls.append(blob['url'])
                    new_count += 1
            
            # Save JSON bytes
            vercel_blob.put(
                list_key,
                json.dumps(urls).encode('utf-8'),
                {"access": "public"}
            )
            
            response = {
                "success": True,
                "new_count": new_count,
                "total_count": len(urls),
                "urls": urls[-5:]  # Dernières 5 pour debug
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
