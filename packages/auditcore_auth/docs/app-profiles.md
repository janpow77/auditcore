# Kompatibilitätsprofile und Befunde der Anwendungen

Grundlage: die ausgeführten `security.py`-Module der Anwendungen an den
gepinnten Commits (`provenance.json`), aufgezeichnet mit
`tools/capture_legacy_auth.py` in `tests/fixtures/legacy_auth_observed.json`
(passlib 1.7.4, python-jose 3.3.0, bcrypt 4.2.1, PyJWT 2.10.1, argon2-cffi 23.1.0).
Die Anwendungen wurden nur gelesen.

## Profile je Anwendung

Alle Profile: HS256, Allowlist nur HS256, kein Leeway, keine Schlüssel-Mindestlänge
(`min_key_bytes=0`, siehe Befund B3). „jose“ = python-jose akzeptierte ein `iat` in
der Zukunft; das Profil behält das bei (`reject_future_iat=False`).

| App | Quelle | Passwortprofil | Token | Claim-Reihenfolge | Laufzeit (Standard) | Pflicht-Claims | iat-Zukunft |
|---|---|---|---|---|---|---|---|
| audit_designer | `backend/app/core/security.py` | `bcrypt-passlib` | access | `* exp iat` | 12 h (`ACCESS_TOKEN_EXPIRE_MINUTES=720`) | exp, iat | jose |
| flownavigator | `apps/backend/app/core/security.py` | `bcrypt-passlib` | access | `* exp` | 24 h | exp, sub | jose |
| flowsearch | `backend/app/core/security.py` | `bcrypt` | access | `* exp` | 30 min | exp, sub | jose |
| qaaudit | `backend/app/core/security.py` | `bcrypt-passlib` | access | `sub role iat exp *` | 24 h | exp, iat, sub | jose |
| versteigerung | `backend/app/core/security.py` | `argon2id` | access | `sub iat exp type=access *` | 30 min | exp, iat, sub | abgelehnt (PyJWT) |
| regulierung | `backend/app/core/security.py` | `bcrypt` | access | `sub role exp iat` | 8 h (Admin: 24 h vom Aufrufer) | exp, iat, sub; `type=refresh` abgelehnt | abgelehnt (PyJWT) |
| regulierung | ebd. `create_refresh_token` | – | refresh | `sub role type=refresh exp iat` | 7 Tage | exp, iat, sub | abgelehnt (PyJWT) |
| flowinvoice | `backend/app/api/user_auth.py` | `bcrypt` | access | `sub role exp iat` | 24 h (`jwt_expire_hours`) | exp, iat, sub | jose |
| audit-portal | `backend/app/api/user_auth.py` | `bcrypt` | access | `sub role exp iat` | 24 h | exp, iat, sub | jose |
| audit-portal | `backend/app/core/security.py` | – | ticket | `* sub exp iat` | 8 h (SSE-Ticket: 60 s vom Aufrufer) | exp, iat, sub | jose |
| flowlib | `python/flowlib/auth.py` | `bcrypt-passlib` | access | `* exp iat` | 24 h | exp, iat | jose |

`*` steht für die übrigen Claims des Aufrufers in ihrer Reihenfolge (z. B. `mfa`,
`tenant_id`, `scope`). Nicht erfasst:

- **cockpit** (`src/cockpit/auth.py`): opake Sitzungstoken in der Datenbank und ein
  Klartext-Adminpasswort aus der Konfiguration (`secrets.compare_digest`); kein JWT,
  kein Hash. Kein Profil; für eine spätere Umstellung: Passwort als argon2id-Hash
  hinterlegen und mit `PasswordHasher(ARGON2ID).verify` prüfen.
- **riskanalysis**: keine Authentifizierung, kein JWT, kein Passwort-Hashing.

### Charakterisierung

| Prüfung | Ergebnis |
|---|---|
| 19 ausgestellte Token der Aufrufstellen (Login, Refresh, SSE-Tickets, Capabilities) | byteweise identisch bei gleichem Zeitpunkt und gleichen Eingaben |
| 153 Prüffälle (17 je App: gültig, abgelaufen, falscher Schlüssel, alg=none, HS512, manipuliert, ohne exp/iat/sub, sub als Zahl, iat/nbf in der Zukunft, Refresh als Access …) | gleiche Entscheidung, Abweichungen nur D1–D3 (siehe `behavior-changes.md`) |
| 90 Passwortfälle (Umlaute, leer, 80 Byte, NUL, defekte Hashes) | alle gespeicherten Hashes werden identisch verifiziert, auch die ersten 72 Byte langer Passwörter; defekte Hashes → `False` (D4) |
| Gegenrichtung (live, `tests/test_legacy_live.py`) | passlib 1.7.4 verifiziert Hashes der Bibliothek, python-jose akzeptiert ihre Token (18 Fälle, lokal ausgeführt) |

Die Mindestversionen der Extras (bcrypt 4.0.1, argon2-cffi 21.1.0, PyJWT 2.6.0,
FastAPI 0.92) wurden mit der vollständigen Testsuite geprüft; bcrypt 3.2.2 scheidet
aus, weil es NUL-Zeichen ablehnt, die flowsearch, regulierung, flowinvoice und
audit-portal bisher gehasht haben.

## Befunde in den Anwendungen (nur gemeldet, nichts geändert)

| Nr. | Schwere | App | Befund |
|---|---|---|---|
| B1 | hoch | flowlib, flowsearch¹, flowinvoice, audit-portal | Nicht gepinntes bcrypt: passlib 1.7.4 bricht mit bcrypt 5 bei *jedem* `hash`/`verify` ab (ValueError aus dem Wraparound-Selbsttest, lokal nachvollzogen). flowinvoice und audit-portal rufen `bcrypt.checkpw` ohne Kürzung auf → mit bcrypt 5 HTTP 500 bei Passwörtern über 72 Byte. regulierung pinnt 4.2.1 und bricht erst beim Upgrade. ¹flowsearch kürzt selbst auf 72 Byte und ist nicht betroffen. |
| B2 | mittel | flowsearch, regulierung, flowinvoice, audit-portal | Ein abgeschnittener Hash in der Datenbank (`$2b$12$…` zu kurz) lässt bcrypt 4.x mit einer Rust-Panic (`PanicException`, eine `BaseException`) abbrechen – `except Exception` fängt sie nicht. Andere defekte Hashes werfen ValueError/UnknownHashError (auch audit_designer, flownavigator, flowlib) → HTTP 500 statt „Anmeldung fehlgeschlagen“. |
| B3 | mittel | audit_designer, versteigerung, qaaudit | Öffentlicher Standardwert des JWT-Schlüssels ohne Startprüfung (`dev-secret-key-change-in-production`, `dev_secret_change_me` mit 20 Byte, `change-me-in-production-…`). Fehlt die Umgebungsvariable, sind Token fälschbar; bei audit_designer hängt zusätzlich die TOTP-Verschlüsselung am selben Schlüssel. regulierung, flowinvoice, audit-portal und flownavigator prüfen den Standardwert. |
| B4 | mittel | audit_designer | `modules/memory/mcp_oauth.py`: bei leerem `MCP_OAUTH_SECRET` nur eine Warnung; HS256 mit leerem Schlüssel macht die OAuth-Token fälschbar. Die Bibliothek lehnt leere Schlüssel ab. |
| B5 | niedrig | flowinvoice, audit-portal | `middleware/user_tracking.py` liest `sub` ohne Signaturprüfung (`verify_signature: False`) für die Nutzerzuordnung im Tracking – Protokolleinträge sind einem beliebigen Nutzer zuschreibbar. |
| B6 | niedrig | flowinvoice, audit-portal | Ausgestellt wird mit `settings.jwt_algorithm`, geprüft mit festem `ALGORITHM = "HS256"`: eine geänderte `JWT_ALGORITHM` sperrt alle Anmeldungen. flowinvoice exportiert zudem ein ungenutztes `core.security.create_access_token` (8 h, ohne Rolle). |
| B7 | niedrig | qaaudit, versteigerung | `extra_claims` überschreiben `sub`, `role`, `iat`, `exp` (bzw. `type`) ungeprüft. Kein heutiger Aufrufer tut das; die Bibliothek verbietet es. |
| B8 | niedrig | alle | Keine App verlangt beim Prüfen ein `exp`; ein Token ohne Ablauf wäre unbegrenzt gültig (heute stellt keine App so eins aus). Die Bibliothek verlangt `exp`. |
| B9 | Info | audit_designer, flowsearch | `datetime.utcnow()` (naiv, ab Python 3.12 veraltet); die Zeitstempel sind trotzdem korrekt. |
| B10 | Info | cockpit | Adminpasswort im Klartext in der Konfiguration (Vergleich zeitkonstant). |
