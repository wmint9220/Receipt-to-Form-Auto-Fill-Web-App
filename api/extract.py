import base64
import json
import os
from http.server import BaseHTTPRequestHandler
import anthropic

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        import cgi
        content_type = self.headers.get('Content-Type', '')
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
            # Parse multipart form
            import email
            from io import BytesIO
            msg = email.message_from_bytes(
                b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + body
            )
            api_key = ''
            image_data = None
            media_type = 'image/jpeg'

            for part in msg.walk():
                name = part.get_param('name', header='content-disposition')
                if name == 'api_key':
                    api_key = part.get_payload(decode=True).decode().strip()
                elif name == 'receipt':
                    image_data = base64.standard_b64encode(
                        part.get_payload(decode=True)
                    ).decode()
                    media_type = part.get_content_type() or 'image/jpeg'

            if not api_key:
                api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if not api_key:
                return send_json({'error': 'No API key provided.'}, 400)
            if not image_data:
                return send_json({'error': 'No image uploaded.'}, 400)

            client = anthropic.Anthropic(api_key=api_key)
            system_prompt = (
                'You are a receipt data extractor. Return ONLY a raw JSON object — '
                'no markdown, no backticks. '
                'Schema: {"merchant":"","date":"YYYY-MM-DD","total":"12.50","currency":"USD","notes":""}. '
                'Use empty string for unknown fields.'
            )
            message = client.messages.create(
                model='claude-opus-4-5',
                max_tokens=512,
                system=system_prompt,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {
                            'type': 'base64',
                            'media_type': media_type,
                            'data': image_data
                        }},
                        {'type': 'text', 'text': 'Extract receipt data. Return only JSON.'}
                    ]
                }]
            )
            raw = message.content[0].text.strip().replace('```json','').replace('```','').strip()
            parsed = json.loads(raw)
            send_json(parsed)

        except Exception as e:
            msg = str(e)
            if 'authentication' in msg.lower() or '401' in msg:
                friendly = 'Invalid API key. Check console.anthropic.com.'
            elif 'rate' in msg.lower() or '429' in msg:
                friendly = 'Rate limit hit. Wait and retry.'
            elif 'credit' in msg.lower():
                friendly = 'No Anthropic credits. Check billing.'
            else:
                friendly = f'{type(e).__name__}: {msg}'
            send_json({'error': friendly}, 500)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
