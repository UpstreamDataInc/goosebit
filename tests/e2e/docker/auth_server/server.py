import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

VALID_TOKEN = os.getenv("AUTH_TOKEN")


class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_response(200, "ok")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if self.path == "/api/v1/auth":
            self._handle_auth()
        else:
            self.send_error(404, "Not found")

    def _handle_auth(self) -> None:
        auth_header = self.headers.get("Authorization")

        if auth_header:
            if not auth_header.startswith("Bearer "):
                self._send_response(401, "Invalid token")
            else:
                if auth_header[7:] == VALID_TOKEN:
                    self._send_response(200, "Authenticated")
                else:
                    self._send_response(401, "Invalid token")
        else:
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length == 0:
                self._send_response(400, "Missing request payload")
                return

            payload = self.rfile.read(content_length)

            try:
                data = json.loads(payload.decode("utf-8"))

                if data.get("token") == VALID_TOKEN:
                    self._send_response(200, "Authenticated")
                else:
                    self._send_response(401, "Invalid token")

            except json.JSONDecodeError:
                self._send_response(400, "Malformed payload")
            except Exception:
                self._send_response(500, "Internal server error")

    def _send_response(self, code: int = 200, message: str = "Unathorized") -> None:
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": message}).encode())


if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 8000), AuthHandler)
    print("Running auth server on port 8000")
    httpd.serve_forever()
