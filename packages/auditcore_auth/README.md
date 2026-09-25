# auditcore_auth

Passwort-Hashing mit benannten Profilen und JWT-Ausstellung/-Prüfung für die
auditcore-Anwendungen. Ersetzt die Abhängigkeiten **python-jose** und **passlib**
(beide nicht mehr gepflegt) durch **PyJWT**, **bcrypt** und **argon2-cffi**.
Keine eigene Kryptografie: Hashen, Salzen, Signieren und zeitkonstante Vergleiche
übernehmen ausschließlich diese Bibliotheken.

Der Kern hat keine Laufzeitabhängigkeiten; die Backends sind Extras und werden
erst beim Gebrauch importiert (fehlt eines, kommt `BackendUnavailableError` mit
dem Namen des Extras):

```bash
pip install 'auditcore_auth[bcrypt,argon2,jwt]'   # Hashes und Token
pip install 'auditcore_auth[fastapi]'             # Bearer-Dependency (inkl. PyJWT)
```

## Passwörter

```python
from auditcore_auth import ARGON2ID, PasswordHasher

hasher = PasswordHasher(ARGON2ID)                # Profil für neue Hashes
stored = hasher.hash("Prüfung-2026")
check = hasher.check("Prüfung-2026", user.password_hash)
if check.valid and check.needs_rehash:           # Rehash bei Login
    user.password_hash = hasher.hash("Prüfung-2026")
```

- Profile: `bcrypt` (bcrypt direkt), `bcrypt-passlib` (Format von passlib,
  NUL-Zeichen abgelehnt), `argon2id` (argon2-cffi-Standard, empfohlen).
- `verify` akzeptiert **jedes** gespeicherte Format (`$2a$`/`$2b$`/`$2y$`,
  `$argon2id$`/`$argon2i$`/`$argon2d$`) unabhängig vom Profil; bcrypt nutzt wie
  bisher die ersten 72 Byte (funktioniert damit auch unter bcrypt 5).
- Fehlender, defekter oder unbekannter Hash → `False` nach einer Blindprüfung
  gleicher Kosten (kein Zeitunterschied „Konto existiert nicht“).
- `verify_and_update` liefert passlib-artig `(gültig, neuer_hash_oder_None)`.

## Token

```python
from datetime import timedelta
from auditcore_auth import DEFAULT_TOKEN_PROFILE, TokenIssuer, TokenVerifier

issuer = TokenIssuer(DEFAULT_TOKEN_PROFILE, settings.secret_key)
issued = issuer.issue({"role": "pruefer"}, subject="42")      # .token, .expires_in
claims = TokenVerifier(DEFAULT_TOKEN_PROFILE, settings.secret_key).verify(issued.token)
claims.subject, claims.claims["role"]
```

`TokenProfile` legt fest: Algorithmus und Allowlist (nie `none`, HMAC und
Public-Key nicht gemischt), Claim-Reihenfolge (`layout`), feste Claims (z. B.
`type=refresh`), Pflicht-Claims (Standard `exp`, `iat`, `sub`; `exp` immer),
Laufzeit, Leeway, Umgang mit `iat` in der Zukunft, abgelehnte Tokentypen,
Schlüssel-Mindestlänge (Standard 32 Byte) und maximale Tokenlänge. Zeitstempel
sind zeitzonenbewusst (UTC); naive `datetime`-Werte werden abgelehnt. Die Uhr ist
injizierbar (`clock=fixed_clock(...)`).

Fehler sind Unterklassen von `TokenError` mit stabilem `reason`
(`expired`, `signature`, `algorithm`, `missing_claim`, …); `verify_or_none`
entspricht den bisherigen `decode_token`-Helfern.

## Kompatibilitätsprofile

```python
from auditcore_auth import PasswordHasher, TokenIssuer, TokenVerifier, app_profile

profile = app_profile("regulierung")
hasher = PasswordHasher(profile.password)
access = TokenIssuer(profile.token("access"), secret).issue(
    {"sub": username, "role": role}, lifetime=timedelta(hours=24))
refresh = TokenIssuer(profile.token("refresh"), secret).issue({"sub": username, "role": role})
TokenVerifier(profile.token("refresh"), secret).verify(token, expected_type="refresh")
```

Profile für audit_designer, flownavigator, flowsearch, qaaudit, versteigerung,
regulierung, flowinvoice, audit-portal und flowlib reproduzieren die bisherigen
Token byteweise und akzeptieren alle bereits ausgestellten Token und
gespeicherten Hashes. Einzelheiten, Charakterisierung und Befunde:
[`docs/app-profiles.md`](docs/app-profiles.md); bewusste Abweichungen:
[`docs/behavior-changes.md`](docs/behavior-changes.md).

## FastAPI

```python
from fastapi import Depends
from auditcore_auth.fastapi_bearer import bearer_dependency

current_token = bearer_dependency(verifier, realm="regulierung")

@app.get("/me")
async def me(token = Depends(current_token)): ...
```

Fehlende oder ungültige Anmeldung → 401 mit `WWW-Authenticate: Bearer …`
(RFC 6750, bei ungültigem Token `error="invalid_token"`); der Ablehnungsgrund
wird dem Client nicht genannt. Das OpenAPI-Schema erhält das Bearer-Schema.

## Sonstiges

`constant_time_equals(a, b)` vergleicht Geheimnisse (CSRF-Token, API-Schlüssel)
über `hmac.compare_digest`, auch für Nicht-ASCII-`str`.
