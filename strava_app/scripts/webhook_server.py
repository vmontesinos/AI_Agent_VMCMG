"""
Simple HTTP webhook server to allow n8n to trigger the Strava sync script.
n8n calls: POST http://strava_sync:8080/sync
"""
import os
import sys
import logging
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

SECRET = os.getenv("SYNC_SECRET")
if not SECRET:
    log.error("SYNC_SECRET environment variable is required but not set. Exiting.")
    sys.exit(1)


class SyncHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/sync":
            auth = self.headers.get("X-Sync-Secret", "")
            if auth != SECRET:
                log.warning("Unauthorized sync attempt from %s", self.client_address[0])
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "unauthorized"}')
                return

            log.info("Sync triggered by %s", self.client_address[0])
            try:
                result = subprocess.run(
                    ["python3", "/app/scripts/sync_strava.py"],
                    capture_output=True, text=True, timeout=300
                )
                status = "ok" if result.returncode == 0 else "error"
                log.info("Sync finished with status: %s", status)
                if result.stderr:
                    log.error("Sync stderr: %s", result.stderr.strip())
                response = {
                    "status": status,
                    "output": result.stdout,
                    "error": result.stderr,
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except subprocess.TimeoutExpired:
                log.error("Sync script timed out after 300s")
                self.send_response(504)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "sync timed out"}')
            except Exception as e:
                log.exception("Unexpected error during sync: %s", e)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        log.info("%s - %s", self.address_string(), format % args)


if __name__ == "__main__":
    log.info("Strava Sync Webhook Server running on port 8080...")
    HTTPServer(("0.0.0.0", 8080), SyncHandler).serve_forever()
