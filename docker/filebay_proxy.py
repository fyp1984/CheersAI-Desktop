import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


UPSTREAM = os.environ.get("FILEBAY_UPSTREAM", "https://uat-filebay.cheersai.cloud").rstrip("/")
LISTEN_HOST = os.environ.get("FILEBAY_PROXY_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("FILEBAY_PROXY_PORT", "39091"))
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class FileBayProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy(head_only=True)

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}", flush=True)

    def _proxy(self, head_only: bool = False):
        target_url = f"{UPSTREAM}{self.path}"
        request_headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }

        try:
            upstream_request = Request(target_url, headers=request_headers, method=self.command)
            with urlopen(upstream_request, timeout=30) as response:
                body = b"" if head_only else response.read()
                self._write_response(response.status, response.headers.items(), body)
        except HTTPError as exc:
            body = b"" if head_only else exc.read()
            self._write_response(exc.code, exc.headers.items(), body)
        except Exception as exc:
            body = str(exc).encode("utf-8", "ignore")
            self._write_response(
                502,
                [("Content-Type", "text/plain; charset=utf-8")],
                body,
            )

    def _write_response(self, status: int, headers, body: bytes):
        self.send_response(status)

        has_content_length = False
        for key, value in headers:
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            if key.lower() == "content-length":
                has_content_length = True
            self.send_header(key, value)

        if not has_content_length:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if body and self.command != "HEAD":
            self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), FileBayProxyHandler)
    print(f"FileBay proxy listening on http://{LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    print(f"Proxying to {UPSTREAM}", flush=True)
    server.serve_forever()
