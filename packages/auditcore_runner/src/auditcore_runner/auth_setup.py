"""Which credentials a new profile uses (RUN-022): GitHub App, then fine-grained PAT, then ``gh``.

Only files in the configuration directory are looked at; their content is
never read here except the App's public identifiers:

* ``github-app.json`` – ``{"app_id": 123, "installation_id": 456, "schluessel_datei": "~/…/app.pem"}``
  (the private key stays in its own file) → ``auth.art = app``
* ``github-token`` – a fine-grained personal access token → ``auth.art = pat``
* otherwise ``gh`` (the user's gh login) – meant for a single machine only.
"""

from __future__ import annotations

import json
from pathlib import Path

from .profile import Auth, config_dir

APP_FILE = "github-app.json"
TOKEN_FILE = "github-token"  # noqa: S105 - file name, not a secret


def _short(path: Path) -> str:
    home = Path.home()
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


def _app(directory: Path) -> Auth | None:
    try:
        data = json.loads((directory / APP_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    app_id, installation, key = data.get("app_id"), data.get("installation_id"), data.get("schluessel_datei")
    if not (isinstance(app_id, int) and isinstance(installation, int) and isinstance(key, str) and key):
        return None
    return Auth("app", "", app_id, key, installation)


def detect_auth(directory: Path | None = None) -> tuple[Auth, str]:
    """Credentials for a proposed profile and why they were chosen."""
    base = directory or config_dir()
    app = _app(base)
    if app is not None:
        return app, f"GitHub App aus {_short(base / APP_FILE)} (empfohlen)"
    token = base / TOKEN_FILE
    if token.is_file():
        return Auth("pat", _short(token)), f"fein granulares Token aus {_short(token)}"
    return Auth("gh"), (
        "gh-Anmeldung – nur für Einzelrechner; empfohlen ist eine GitHub App "
        f"({_short(base / APP_FILE)}) oder ein Token ({_short(token)})"
    )
