from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        body = json.dumps({"message": "Python OK !"})
        self.wfile.write(body.encode("utf-8"))
        return
