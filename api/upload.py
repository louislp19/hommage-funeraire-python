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
            
            # Clé globale pour la liste d'images (accumulate)
            list_key = "GLOBAL_MEMORIAL_IMAGES"
            
            # Charger liste existante
            try:
                existing_data = vercel_blob.get(list_key)
                urls = json.loads(existing_data)
            except:
                urls = []
            
            new_count = 0
            
            # Traiter tous les fichiers (multi-upload)
            files = form.list or []
            for file in files:
                if file.filename:
                    # Nom unique avec random suffix
                    pathname = f"memorial/{uuid.uuid4().hex}-{file.filename}"
                    blob = vercel_blob.put(
                        pathname,
                        file.file.read(),
                        {
                            "access": "public",
                            "addRandomSuffix": "true",  # Fix duplicate !
                            "contentType": file.type or "image/jpeg"
                        }
                    )
                    urls.append(blob['url'])
                    new_count += 1
            
            # Sauvegarder liste mise à jour
            vercel_blob.put(
                list_key,
                json.dumps(urls),
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
