import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Force use of OpenSSL instead of schannel on Windows
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
    print("✓ Using OpenSSL backend for SSL connections")
except ImportError:
    print("⚠ pyOpenSSL not available, using system SSL (may fail on some servers)")
except Exception as e:
    print(f"⚠ Failed to inject pyOpenSSL: {e}")

import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    
    def do_POST(self):
        self._proxy()
    
    def do_PUT(self):
        self._proxy()
    
    def do_DELETE(self):
        self._proxy()

    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}", flush=True)

    def _proxy(self, head_only: bool = False):
        target_url = f"{UPSTREAM}{self.path}"
        request_headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }

        # Read request body for POST/PUT
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        try:
            response = requests.request(
                method=self.command,
                url=target_url,
                headers=request_headers,
                data=body,
                timeout=30,
                verify=False,
                allow_redirects=False
            )
            
            response_body = b"" if head_only else response.content
            self._write_response(response.status_code, response.headers.items(), response_body)
        except requests.RequestException as exc:
            error_body = str(exc).encode("utf-8", "ignore")
            self._write_response(
                502,
                [("Content-Type", "text/plain; charset=utf-8")],
                error_body,
            )
        except Exception as exc:
            error_body = str(exc).encode("utf-8", "ignore")
            self._write_response(
                502,
                [("Content-Type", "text/plain; charset=utf-8")],
                error_body,
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
