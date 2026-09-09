import json
import os
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 8765

SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "wallets.jsonl"
)


# ============================================================
# Request handler
# ============================================================

class SaveHandler(BaseHTTPRequestHandler):

    # --------------------------------------------------------
    # CORS headers so the extension pages can POST here
    # --------------------------------------------------------

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # --------------------------------------------------------
    # Preflight
    # --------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    # --------------------------------------------------------
    # Append a record to the shared file
    # --------------------------------------------------------

    def do_POST(self):
        if self.path != "/save":
            self.send_response(404)
            self._send_cors()
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            record = json.loads(raw.decode("utf-8"))
        except Exception as e:
            print("Bad record received:", e)

            self.send_response(400)
            self._send_cors()
            self.end_headers()
            return

        record["receivedAt"] = (
            datetime.datetime.now().isoformat(timespec="seconds")
        )

        # One JSON line per profile, append mode.
        # The server is single-threaded, so concurrent
        # posts from several profiles are queued and
        # never interleave inside the file.
        with open(SAVE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(
            "Saved profile",
            record.get("profileId"),
            "->",
            SAVE_FILE
        )

        self.send_response(200)
        self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    # Quiet default request logging
    def log_message(self, fmt, *args):
        pass


# ============================================================
# Start server
# ============================================================

print("Append-save server running on http://" + HOST + ":" + str(PORT))
print("All records are appended to:")
print(SAVE_FILE)
print("Press Ctrl+C to stop.")

HTTPServer((HOST, PORT), SaveHandler).serve_forever()
