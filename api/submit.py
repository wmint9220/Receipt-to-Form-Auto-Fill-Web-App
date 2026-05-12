import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        def send_json(data, status=200):
            payload = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(payload)

        try:
            data = json.loads(body)
            entry = {
                'merchant':     data.get('merchant', ''),
                'date':         data.get('date', ''),
                'total':        data.get('total', ''),
                'currency':     data.get('currency', 'USD'),
                'notes':        data.get('notes', ''),
                'submitted_at': datetime.now().strftime('%b %d, %Y %I:%M %p'),
            }
            send_json({'success': True, 'submission': entry})
        except Exception as e:
            send_json({'error': str(e)}, 500)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
