import os
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Test TOKEN existe
            token = os.environ.get("BLOB_READ_WRITE_TOKEN", "MANQUANT")
            
            response = {
                "success": True, 
                "message": "API + token OK",
                "token_status": "OK" if token != "MANQUANT" else "MANQUANT",
                "token_preview": token[:20] + "..." if token != "MANQUANT" else None
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
