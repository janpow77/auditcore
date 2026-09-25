# auditcore_auth

## Zweck

Passwort-Hashing mit benannten Profilen (bcrypt, argon2id) und JWT-Ausstellung/-Prüfung über PyJWT, mit Kompatibilitätsprofilen, unter denen bisherige Hashes und Token der Anwendungen gültig bleiben.

Für die Backends von audit_designer, flownavigator, flowsearch, qaaudit,
versteigerung, regulierung, flowinvoice, audit-portal und flowlib; ersetzt dort
python-jose und passlib (beide nicht mehr gepflegt). Keine eigene
Kryptografie, keine Benutzerverwaltung, keine Sitzungs- oder
Rechteverwaltung – das bleibt in der Anwendung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_auth[bcrypt,argon2,jwt]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Version 0.1.0 ist noch in keinem Release veröffentlicht. Nach der
Veröffentlichung steht die Direkt-URL mit Hash im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-auth/`; Muster für eine
hashgebundene `requirements.txt`:

```text
auditcore_auth @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_auth-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); die Backends sind dort
Suggests (`python3-bcrypt` ≥ 4.0.1, `python3-argon2`, `python3-jwt`,
`python3-fastapi`):

```bash
sudo apt-get install python3-auditcore-auth python3-bcrypt python3-argon2 python3-jwt
```

Extras: `[bcrypt]` – bcrypt-Hashes über bcrypt ≥ 4.0.1; `[argon2]` – argon2id
über argon2-cffi; `[jwt]` – Token über PyJWT; `[fastapi]` – Bearer-Dependency
(FastAPI und PyJWT); `[dev]` – Test- und Prüfwerkzeuge. Fehlt ein Backend,
meldet der erste Aufruf `BackendUnavailableError` mit dem Namen des Extras.

## Schnellstart

Ohne Extras (Profile, Formaterkennung, Konfigurationsprüfung):

```python
from datetime import timedelta
from auditcore_auth import (
    ConfigurationError, HashScheme, TokenProfile, app_profile, constant_time_equals,
    identify_hash,
)

profile = app_profile("regulierung")
assert profile.password.name == "bcrypt"
assert profile.token("refresh").lifetime == timedelta(days=7)
assert profile.token("access").rejected_types == ("refresh",)

info = identify_hash("$2b$12$tykvNDpREeaFzESOYJImI.kzQ1zN4yEwmBO6UHdoYyoYK7TmEubSO")
assert info.scheme is HashScheme.BCRYPT and info.bcrypt_rounds == 12
assert identify_hash("$2b$12$short") is None      # nie an bcrypt weitergereicht

try:
    TokenProfile("unsicher", lifetime=timedelta(minutes=5), algorithm="none",
                 accepted_algorithms=("none",))
except ConfigurationError:
    pass
else:
    raise AssertionError("alg=none darf nie zulässig sein")
assert constant_time_equals("Prüfung", "Prüfung")
```

Mit den Extras `[bcrypt,argon2,jwt]`:

```python no-run
from auditcore_auth import ARGON2ID, PasswordHasher, TokenIssuer, TokenVerifier

hasher = PasswordHasher(ARGON2ID)
check = hasher.check(password, user.password_hash)      # jedes gespeicherte Format
if check.valid and check.needs_rehash:                   # Rehash bei Login
    user.password_hash = hasher.hash(password)

access = profile.token("access")
issued = TokenIssuer(access, secret).issue({"role": role}, subject=username)
claims = TokenVerifier(access, secret).verify(issued.token)   # TokenError bei Ablehnung
```

FastAPI (`[fastapi]`): `bearer_dependency(verifier)` aus
`auditcore_auth.fastapi_bearer` liefert den geprüften `VerifiedToken` oder 401
mit `WWW-Authenticate: Bearer` (RFC 6750, `error="invalid_token"`).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_auth.__all__` (39):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `APP_PROFILES` | Konstante | – | `compat` |
| `ARGON2ID` | Konstante | argon2id with argon2-cffi defaults; also passlib's ``argon2`` scheme (versteigerung). Recommended for new applications. | `password_profiles` |
| `BCRYPT` | Konstante | bcrypt called directly (regulierung, flowinvoice, audit-portal, flowsearch). | `password_profiles` |
| `BCRYPT_PASSLIB` | Konstante | bcrypt as passlib's ``CryptContext(schemes=["bcrypt"])`` produced it (audit_designer, flownavigator, qaaudit, flowlib): same ``$2b$12$`` format, NUL bytes refused. | `password_profiles` |
| `DEFAULT_TOKEN_PROFILE` | Konstante | Recommended for new code: HS256 only, exp/iat/sub required, 30 minutes, no leeway. | `token_profiles` |
| `PASSWORD_PROFILES` | Konstante | – | `password_profiles` |
| `AppProfile` | Datenklasse | Password and token profiles of one application. | `compat` |
| `Argon2Parameters` | Datenklasse | argon2 cost parameters; the defaults equal argon2-cffi's RFC 9106 low-memory profile. | `password_profiles` |
| `AuthError` | Ausnahme | Base class of every error raised by auditcore_auth. | `errors` |
| `BackendUnavailableError` | Ausnahme | An optional backend (bcrypt, argon2-cffi, PyJWT, FastAPI) is not installed. | `errors` |
| `Clock` | Typalias | – | `clock` |
| `ConfigurationError` | Ausnahme | A profile, key or parameter is unusable or unsafe. | `errors` |
| `DisallowedAlgorithmError` | Ausnahme | – | `errors` |
| `ExpiredTokenError` | Ausnahme | – | `errors` |
| `HashInfo` | Datenklasse | What a stored hash string declares about itself. | `password_profiles` |
| `HashScheme` | Aufzählung | Hash families the library can produce and verify. | `password_profiles` |
| `ImmatureTokenError` | Ausnahme | – | `errors` |
| `InvalidClaimError` | Ausnahme | – | `errors` |
| `InvalidSignatureError` | Ausnahme | – | `errors` |
| `IssuedToken` | Datenklasse | A freshly signed token and its validity window. | `tokens` |
| `MalformedTokenError` | Ausnahme | – | `errors` |
| `MissingClaimError` | Ausnahme | – | `errors` |
| `PasswordCheck` | Datenklasse | Result of :meth:`PasswordHasher.check`. | `passwords` |
| `PasswordHasher` | Klasse | Hash new passwords under one profile; verify hashes of any known format. | `passwords` |
| `PasswordPolicyError` | Ausnahme | The password cannot be hashed under the selected profile. | `errors` |
| `PasswordProfile` | Datenklasse | How new password hashes are created. | `password_profiles` |
| `TokenError` | Ausnahme | A token was rejected; ``reason`` is a stable machine-readable code. | `errors` |
| `TokenIssuer` | Klasse | Sign tokens; the payload order follows ``profile.layout``. | `tokens` |
| `TokenProfile` | Datenklasse | Issuing and verification rules for one kind of token. | `token_profiles` |
| `TokenTypeError` | Ausnahme | – | `errors` |
| `TokenVerifier` | Klasse | Verify tokens: allowlisted algorithm, signature, required claims, time window. | `tokens` |
| `VerifiedToken` | Datenklasse | Claims of a token whose signature, algorithm and time window were checked. | `tokens` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `app_profile` | Funktion | Compatibility profile of ``app`` (e.g. ``"regulierung"``). | `compat` |
| `constant_time_equals` | Funktion | Compare two secrets without leaking the position of the first difference. | `compare` |
| `fixed_clock` | Funktion | Return a clock that always answers ``instant`` (for tests and replays). | `clock` |
| `identify_hash` | Funktion | Recognise a stored hash by its full syntax; ``None`` if it is not well-formed. | `password_profiles` |
| `password_profile` | Funktion | Look up a named profile. | `password_profiles` |
| `system_clock` | Funktion | Return the current time as an aware UTC datetime. | `clock` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_auth.clock` | Timezone-aware clock handling. |
| `auditcore_auth.compare` | Constant-time comparison for secrets such as CSRF tokens or API keys. |
| `auditcore_auth.compat` | Compatibility profiles of the nine applications (characterised, see docs/app-profiles.md). |
| `auditcore_auth.errors` | Error contract of auditcore_auth. |
| `auditcore_auth.fastapi_bearer` | Optional FastAPI integration: a Bearer-token dependency (extra ``fastapi``). |
| `auditcore_auth.password_profiles` | Named password hashing profiles and hash-format recognition (stdlib only). |
| `auditcore_auth.passwords` | Password hashing and verification with named profiles. |
| `auditcore_auth.token_profiles` | JWT profiles: algorithm allowlist, claim layout, required claims, lifetime, leeway. |
| `auditcore_auth.tokens` | Issue and verify JWTs under a :class:`TokenProfile` (PyJWT backend). |
<!-- api-overview:end -->

## Profile und Konfiguration

- **Passwortprofile:** `bcrypt` (bcrypt direkt, Kosten 12, `$2b$`),
  `bcrypt-passlib` (Format von passlib, NUL-Zeichen abgelehnt), `argon2id`
  (argon2-cffi-Standard `m=65536,t=3,p=4`, empfohlen). Verifiziert wird jedes
  Format unabhängig vom Profil; bcrypt nutzt wie bisher die ersten 72 Byte.
- **Tokenprofil** (`TokenProfile`): Algorithmus und Allowlist (nie `none`,
  HMAC und Public-Key nicht gemischt), Claim-Reihenfolge, feste Claims,
  Pflicht-Claims (`exp` immer; Standard exp, iat, sub), Laufzeit, Leeway,
  `iat` in der Zukunft, abgelehnte Tokentypen, Schlüssel-Mindestlänge
  (Standard 32 Byte), maximale Tokenlänge. `DEFAULT_TOKEN_PROFILE`: HS256,
  30 Minuten.
- **Kompatibilitätsprofile** (`app_profile(app)`) für neun Anwendungen:
  Tabelle in [`docs/app-profiles.md`](docs/app-profiles.md).
- Uhr injizierbar (`clock=fixed_clock(...)`), Zeitstempel immer UTC,
  naive `datetime`-Werte werden abgelehnt. Keine Umgebungsvariablen; Schlüssel
  und Laufzeiten übergibt die Anwendung.

## Herkunft und Charakterisierung

Neuimplementierung gegen charakterisierte Verträge. `tools/capture_legacy_auth.py`
führt die `security.py`-Module der neun Anwendungen an den in `provenance.json`
gepinnten Commits aus (nur lesend über `git show`, mit passlib 1.7.4,
python-jose 3.3.0, bcrypt 4.2.1, PyJWT 2.10.1, argon2-cffi 23.1.0);
Fixture `tests/fixtures/legacy_auth_observed.json`:

- 19 ausgestellte Token der echten Aufrufstellen – von der Bibliothek byteweise
  identisch erzeugt (`tests/test_legacy_tokens.py`),
- 153 Prüffälle – gleiche Entscheidung bis auf D1–D3,
- 90 Passwortfälle – alle gespeicherten Hashes identisch verifiziert
  (`tests/test_legacy_passwords.py`),
- Gegenrichtung live (`tests/test_legacy_live.py`, nur mit passlib/jose):
  passlib und python-jose akzeptieren Hashes und Token der Bibliothek.

cockpit und riskanalysis wurden geprüft; sie enthalten kein JWT und kein
Passwort-Hashing. Befunde in den Anwendungen: [`docs/app-profiles.md`](docs/app-profiles.md).

## Bewusste Verhaltensabweichungen

Token ohne `exp` werden abgelehnt; Token ohne `iat`/`sub` dort, wo die App
diese Claims immer ausgestellt hat; defekte Hashes ergeben `False` statt einer
Exception; reservierte Claims kann der Aufrufer nicht überschreiben. Kein
bereits ausgestelltes Token und kein gespeicherter Hash ist betroffen.
Vollständig in [`docs/behavior-changes.md`](docs/behavior-changes.md) (D1–D7).

## Abhängigkeiten

Python ≥ 3.11; zur Laufzeit keine Pflichtabhängigkeiten. Extras: bcrypt ≥ 4.0.1
(3.x lehnt NUL-Zeichen ab, die Anwendungen bisher gehasht haben),
argon2-cffi ≥ 21.1, PyJWT ≥ 2.6, FastAPI ≥ 0.92. Die Mindestversionen sind mit
der vollständigen Testsuite geprüft. python-jose und passlib sind bewusst keine
Abhängigkeit (auch nicht für Tests in der CI).

## Sicherheit und Datenschutz

Hashen, Salzen, Signieren und zeitkonstante Vergleiche übernehmen bcrypt,
argon2-cffi, PyJWT und `hmac.compare_digest`; das Paket implementiert keine
Kryptografie. Kein Netzwerk, keine Dateien, kein Zustand außer einem
zwischengespeicherten Blind-Hash. Fehlende oder defekte Hashes werden mit einer
Blindprüfung gleicher Kosten beantwortet. Die Gründe einer Tokenablehnung
(`TokenError.reason`) sind für Protokolle gedacht; die FastAPI-Dependency gibt
sie nicht an Clients weiter. Leere Schlüssel werden immer abgelehnt; die
Kompatibilitätsprofile verlangen keine Schlüssel-Mindestlänge, weil die
Anwendungen heute kürzere Standardschlüssel zulassen (Befund B3). Passwörter
und Token werden nicht gespeichert oder protokolliert.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat am 22.09.2026 entschieden, dass die
Bibliotheken unter MIT stehen, die Anwendungen nicht (`USER_AUTHORIZED_MIT`
nur für diese Bibliothek). Quellen und Erklärung: `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
