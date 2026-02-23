from http.server import BaseHTTPRequestHandler
import json
import time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Réponse FAKE mais JSON valide
            memorial_id = "test"
            timestamp = int(time.time() * 1000)
            fake_url = f"https://blob.vercel-storage.com/memorials/{memorial_id}/{timestamp}-photo.jpg"
            
            response = {
                "success": True,
                "message": "Upload reçu (test sans fichier)",
                "uploads": [{
                    "url": fake_url,
                    "pathname": f"memorials/{memorial_id}/{timestamp}-photo.jpg",
                    "name": "test.jpg"
                }]
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
