"""Demo- und Integrationsserver: auditcore_kanban.rest.KanbanApi über http.server.

    python packages-js/ui/demo/kanban_api_server.py --port 18766

Nur Standardbibliothek plus auditcore_kanban (pip install -e packages/auditcore_kanban).
Die Identität kommt aus der Kopfzeile ``X-Demo-User`` (nur Demo – keine Anmeldung).
Pfade: ``/api/kanban/...`` wie im REST-Vertrag docs/kanban/rest-api.md.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

from auditcore_kanban import BoardService, InMemoryBoardStore
from auditcore_kanban.rest import KanbanApi

PREFIX = "/api/kanban"
USERS = {"anna", "markus", "lena", "tobias"}
API = KanbanApi(BoardService(InMemoryBoardStore(), user_exists=USERS.__contains__))


class Handler(BaseHTTPRequestHandler):
    def _dispatch(self) -> None:
        url = urlsplit(self.path)
        if not url.path.startswith(PREFIX):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        body = json.loads(raw) if raw else None
        response = API.handle(
            self.command,
            url.path[len(PREFIX):] or "/",
            user_id=self.headers.get("X-Demo-User"),
            query=dict(parse_qsl(url.query)),
            body=body,
            if_match=self.headers.get("If-Match"),
        )
        payload = b"" if response.status == 204 else json.dumps(response.body).encode()
        self.send_response(response.status)
        for name, value in response.headers.items():
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _dispatch

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - Signatur der Basisklasse
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18766)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
