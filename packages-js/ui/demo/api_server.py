"""Demo-Backend für die Seiten Stichprobe und Benford der Komponenten-Demo.

Startet die REST-Router von auditcore_sampling.web und auditcore_statistics.web
unter /api/sampling und /api/benford (Extra ``web`` beider Pakete und uvicorn
erforderlich). Nur für Demo und Browserprüfung, ohne Authentisierung.

    python demo/api_server.py            # Port 18765, sonst FA_DEMO_API_PORT
"""

from __future__ import annotations

import os

import uvicorn
from auditcore_sampling.web import routes as sampling_routes
from auditcore_statistics.web import routes as benford_routes
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(
    routes=[
        Mount("/api/sampling", routes=sampling_routes()),
        Mount("/api/benford", routes=benford_routes()),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("FA_DEMO_API_PORT", "18765")))
