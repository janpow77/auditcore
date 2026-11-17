"""Proxy Playwright Chromium archive requests to the official GCS bucket."""

import re
import shutil
from http.client import HTTPException, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_PREFIX = "/builds/cft/"
_FFMPEG_PREFIX = "/dbazure/download/playwright/builds/ffmpeg/"
_PATH_PART = re.compile(r"[A-Za-z0-9._-]+")


class _Handler(BaseHTTPRequestHandler):
    """Rewrite only Playwright CFT paths to their official bucket paths."""

    protocol_version = "HTTP/1.0"

    def do_GET(self) -> None:
        path = self.path.split("?", maxsplit=1)[0]
        if path.startswith(_PREFIX):
            host = "storage.googleapis.com"
            upstream_path = "/chrome-for-testing-public/" + path.removeprefix(
                _PREFIX
            )
        elif path.startswith(_FFMPEG_PREFIX):
            host = "playwright.download.prss.microsoft.com"
            upstream_path = path
        else:
            self.send_error(404)
            return

        parts = upstream_path.lstrip("/").split("/")
        if not all(
            part not in {".", ".."} and _PATH_PART.fullmatch(part)
            for part in parts
        ):
            self.send_error(404)
            return

        connection = HTTPSConnection(host, timeout=60)
        try:
            headers = {}
            if range_header := self.headers.get("Range"):
                headers["Range"] = range_header
            connection.request(
                "GET", upstream_path, headers=headers
            )
            response = connection.getresponse()
            if response.status not in {200, 206}:
                self.send_error(502)
                return
            self.send_response(response.status)
            self.send_header("Content-Type", "application/zip")
            if content_length := response.getheader("Content-Length"):
                self.send_header("Content-Length", content_length)
            if content_range := response.getheader("Content-Range"):
                self.send_header("Content-Range", content_range)
            self.end_headers()
            shutil.copyfileobj(response, self.wfile, length=1024 * 1024)
        except (HTTPException, OSError):
            self.send_error(502)
        finally:
            connection.close()

    def log_message(self, format: str, *args: object) -> None:
        del format, args


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8765), _Handler).serve_forever()
