"""Demo-Backend für die REST-Seiten der Komponenten-Demo.

Startet die REST-Router von auditcore_sampling.web (/api/sampling),
auditcore_statistics.web (/api/benford) und auditcore_registry_sources.web
(/api/screening, erfundene Demo-Daten aus screening_demo.py),
auditcore_dataprotection.web (/api/dataprotection, dataprotection_demo.py),
auditcore_documents.web (/api/synopsis, synthetische Dokumente aus
documents_demo.py; Belegerkennung unter /api/extraction mit Attrappen-Ports aus
extraction_demo.py) und auditcore_geo.web (/api/geo, synthetische Kacheln und
GeoPackage-Dateien aus geo_demo.py unter /api/geo-demo). Erforderlich: Extra ``web`` der Pakete
und uvicorn. Nur für Demo und Browserprüfung.

    python demo/api_server.py            # Port 18765, sonst FA_DEMO_API_PORT
"""

from __future__ import annotations

import os

import uvicorn
from auditcore_sampling.web import routes as sampling_routes
from auditcore_statistics.web import routes as benford_routes
from dataprotection_demo import dataprotection_routes
from documents_demo import comparison_routes
from extraction_demo import extraction_routes_demo
from geo_demo import geo_routes_demo
from screening_demo import screening_routes
from starlette.applications import Starlette
from starlette.routing import Mount

GEO, GEO_DEMO = geo_routes_demo()

app = Starlette(
    routes=[
        Mount("/api/sampling", routes=sampling_routes()),
        Mount("/api/benford", routes=benford_routes()),
        Mount("/api/screening", routes=screening_routes()),
        Mount("/api/dataprotection", routes=dataprotection_routes()),
        Mount("/api/synopsis", routes=comparison_routes()),
        Mount("/api/extraction", routes=extraction_routes_demo()),
        Mount("/api/geo", routes=GEO),
        Mount("/api/geo-demo", routes=GEO_DEMO),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("FA_DEMO_API_PORT", "18765")))
