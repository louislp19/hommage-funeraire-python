import os
import json
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import vercel_blob
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            form = FieldStorage(
                fp=self.rfile, 
                headers=self.headers, 
                environ={'REQUEST_METHOD':'POST'}
            )
            
            # Clé JSON accumulateur
            list_key = "GLOBAL_MEMORIAL_IMAGES"
            
            # Load existant
            try:
                existing_data = vercel_blob.get(list_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_count = 0
            
            # Parcourir TOUS fields (files)
            for key in form.keys():
                file_item = form[key]
                if file_item.filename:  # C'est un fichier
                    # Nom unique
                    pathname = f"memorial/{uuid.uuid4().hex}-{file_item.filename}"
                    
                    # LIRE EN BYTES → FIX ERREUR !
                    file_bytes = file_item.file.read()
                    
                    # Upload avec options
                    blob = vercel_blob.put(
                        pathname,
                        file_bytes,  # Bytes direct
                        {
                            "access": "public",
                            "addRandomSuffix": "true",
                            "contentType": file_item.type or "image/jpeg"
                        }
                    )
                    urls.append(blob['url'])
                    new_count += 1
            
            # Save JSON list
            vercel_blob.put(
                list_key,
                json.dumps(urls).encode('utf-8'),  # Bytes aussi !
                {"access": "public"}
            )
            
            response = {
                "success": True,
                "new_count": new_count,
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

def main():
    handler().do_POST()

if __name__ == "__main__":
    main()
