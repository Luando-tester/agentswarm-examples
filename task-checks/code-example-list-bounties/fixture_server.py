"""Private-memory loopback fixture, running in its own network-none container."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

fixtures = json.loads(Path("/fixtures.json").read_text())


class Handler(BaseHTTPRequestHandler):
    def handle_request(self):
        print("REQUEST " + json.dumps({"method": self.command, "path": self.path,
                                      "authorization": bool(self.headers.get("Authorization"))}), flush=True)
        prefix = self.path.removesuffix("/api/bounties")
        fixture = fixtures.get(prefix)
        if self.command != "GET" or not fixture:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(fixture["status"])
        body = fixture["body"].encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = handle_request

    def log_message(self, *_):
        pass


server = HTTPServer(("127.0.0.1", 8765), Handler)
print("READY", flush=True)
server.serve_forever()
