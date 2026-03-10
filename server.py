#!/usr/bin/env python3
"""
Weaverly dev server — serves static files + exposes .env keys via /api/env
Usage: python3 server.py [port]
"""
import http.server
import json
import os
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(ROOT, '.env')

def load_env():
    # Start with real environment variables (works on Render, Railway, etc.)
    env = {k: v for k, v in os.environ.items()}
    # Then overlay with .env file values (local dev)
    try:
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path

        # Root → redirect to main page
        if path == '/' or path == '':
            self.send_response(302)
            self.send_header('Location', '/weaverly-hero-production.html')
            self.end_headers()
            return

        if path == '/api/env':
            env = load_env()
            payload = {
                'anthropicKey': env.get('ANTHROPIC_API_KEY', ''),
                'openaiKey':    env.get('OPENAI_API_KEY', ''),
            }
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(body))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Only log non-asset requests
        if not any(args[0].endswith(ext) for ext in ('.png','.jpg','.ico','.woff2','.css')):
            super().log_message(fmt, *args)

if __name__ == '__main__':
    # Render/Railway pass port via $PORT env var; fallback to arg or 8765 for local dev
    port = int(os.environ.get('PORT', sys.argv[1] if len(sys.argv) > 1 else 8765))
    os.chdir(ROOT)
    with http.server.ThreadingHTTPServer(('', port), Handler) as httpd:
        print(f'  Weaverly dev server → http://localhost:{port}')
        print(f'  Serving: {ROOT}')
        print(f'  .env loaded: {"yes" if os.path.exists(ENV_FILE) else "no"}')
        print()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Server stopped.')
