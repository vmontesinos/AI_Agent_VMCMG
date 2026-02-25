"""
Simple HTTP webhook server to allow n8n to trigger the Strava sync script.
n8n calls: POST http://strava_sync:8080/sync
"""
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

SECRET = os.getenv("SYNC_SECRET", "change-me-please")

class SyncHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/sync":
            # Check optional secret header
            auth = self.headers.get("X-Sync-Secret", "")
            if auth != SECRET:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"error": "unauthorized"}')
                return

            try:
                result = subprocess.run(
                    ["python3", "/app/scripts/sync_strava.py"],
                    capture_output=True, text=True, timeout=300
                )
                response = {
                    "status": "ok" if result.returncode == 0 else "error",
                    "output": result.stdout,
                    "error": result.stderr
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default logs

if __name__ == "__main__":
    print("Strava Sync Webhook Server running on port 8080...")
    HTTPServer(("0.0.0.0", 8080), SyncHandler).serve_forever()
