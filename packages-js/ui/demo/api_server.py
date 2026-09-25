"""Demo-Backend für die REST-Seiten der Komponenten-Demo.

Startet die REST-Router von auditcore_sampling.web (/api/sampling),
auditcore_statistics.web (/api/benford) und auditcore_registry_sources.web
(/api/screening, erfundene Demo-Daten aus screening_demo.py). Erforderlich:
Extra ``web`` der drei Pakete und uvicorn. Nur für Demo und Browserprüfung.

    python demo/api_server.py            # Port 18765, sonst FA_DEMO_API_PORT
"""

from __future__ import annotations

import os

import uvicorn
from auditcore_sampling.web import routes as sampling_routes
from auditcore_statistics.web import routes as benford_routes
from screening_demo import screening_routes
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(
    routes=[
        Mount("/api/sampling", routes=sampling_routes()),
        Mount("/api/benford", routes=benford_routes()),
        Mount("/api/screening", routes=screening_routes()),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("FA_DEMO_API_PORT", "18765")))
