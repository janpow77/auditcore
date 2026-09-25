"""Pinned legacy sources of the nine applications (read-only, via ``git show``).

Each entry names the GitHub repository, the pushed commit, the local checkout
directory below ``--repos-root`` and the files whose executed behaviour is
captured by ``capture_legacy_auth.py``.
"""

from __future__ import annotations

SOURCES: dict[str, dict[str, object]] = {
    "audit_designer": {
        "repository": "janpow77/audit_designer",
        "commit": "ccd65245182982af3ef885a7a6d43583f4f72cbb",
        "checkout": "audit_designer",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/core/config.py",
                  "backend/app/api/auth.py", "backend/app/api/vpai_notebook/jupyter.py"],
    },
    "flownavigator": {
        "repository": "janpow77/flownavigator",
        "commit": "9dff858d3772e59533886dfbae70c672d574a1d4",
        "checkout": "flownavigator",
        "security": "apps/backend/app/core/security.py",
        "files": ["apps/backend/app/core/security.py", "apps/backend/app/core/config.py",
                  "apps/backend/app/services/auth_service.py", "apps/backend/app/api/vendor.py"],
    },
    "flowsearch": {
        "repository": "janpow77/flowsearch",
        "commit": "9ac5e0dd0c2b7363b5a077551e4fb7103f32c697",
        "checkout": "flowsearch",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/core/config.py",
                  "backend/app/api/auth.py"],
    },
    "qaaudit": {
        "repository": "janpow77/qaaudit",
        "commit": "c78be5c86454d457e5c66d0c65b5117a8528d462",
        "checkout": "qaaudit",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/core/config.py",
                  "backend/app/api/v1/auth.py"],
    },
    "versteigerung": {
        "repository": "janpow77/versteigerung",
        "commit": "729f9a10bc5478bd724ef40c1f4cd572e5a3dada",
        "checkout": "versteigerung",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/core/config.py",
                  "backend/app/api/routers/auth.py"],
    },
    "regulierung": {
        "repository": "janpow77/regulierung",
        "commit": "ce76e48c8ad7f1cbe430948158a4e7001a02ba99",
        "checkout": "regulierung",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/config.py",
                  "backend/app/core/auth/jwt_backend.py", "backend/app/api/auth_routes.py"],
    },
    "flowinvoice": {
        "repository": "janpow77/flowinvoice",
        "commit": "5d5d8c5aded2b7eee82c0813994e9efd549277b3",
        "checkout": "flowinvoice",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/config.py",
                  "backend/app/api/user_auth.py", "backend/app/api/deps.py"],
    },
    "audit-portal": {
        "repository": "janpow77/audit-portal",
        "commit": "72cc4b1a15fdcd5ee06ef8124d864904cc4e1312",
        "checkout": "audit-portal",
        "security": "backend/app/core/security.py",
        "files": ["backend/app/core/security.py", "backend/app/config.py",
                  "backend/app/api/user_auth.py", "backend/app/api/deps.py"],
    },
    "flowlib": {
        "repository": "janpow77/flowlib",
        "commit": "aca2dc6aad25aea0720312dbcc6da00b0bcba330",
        "checkout": "flowlib",
        "security": "python/flowlib/auth.py",
        "files": ["python/flowlib/auth.py"],
    },
}

# Read for the inventory, no JWT or password hash to characterise.
REFERENCE_ONLY: dict[str, dict[str, object]] = {
    "cockpit": {
        "repository": "janpow77/cockpit",
        "commit": "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406",
        "checkout": "cockpit",
        "files": ["src/cockpit/auth.py"],
        "finding": "Opake Sitzungstoken in der Datenbank und Klartext-Adminpasswort "
                   "aus der Konfiguration (secrets.compare_digest); kein JWT, kein Hash.",
    },
    "riskanalysis": {
        "repository": "janpow77/riskanalysis",
        "commit": "dace0f66abde171ab91685483092ad7c3550ce55",
        "checkout": "riskanalysis",
        "files": [],
        "finding": "Keine Authentifizierung, kein JWT und kein Passwort-Hashing im Backend.",
    },
}
