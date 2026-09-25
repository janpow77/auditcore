# Abweichungen vom Original (bewusst)

Grundlage: `tests/fixtures/legacy_auth_observed.json` (ausgeführte Originale,
siehe `app-profiles.md`). Gleiches Verhalten prüfen
`tests/test_legacy_passwords.py` und `tests/test_legacy_tokens.py`; die
Abweichungen sind dort mit dem beobachteten Altwert festgehalten.

| Nr. | Original (beobachtet) | Bibliothek | Grund | Betrifft ausgestellte Token/Hashes? |
|---|---|---|---|---|
| D1 | Token ohne `exp` werden akzeptiert (python-jose und PyJWT prüfen `exp` nur, wenn vorhanden) | abgelehnt: `exp` ist in jedem Profil Pflicht | Kein unbegrenzt gültiges Token | nein – jede App stellte `exp` aus |
| D2 | Token ohne `iat` werden akzeptiert | abgelehnt, wo die App immer `iat` ausstellte (alle außer flownavigator, flowsearch) | Pflicht-Claims exp/iat/sub | nein |
| D3 | Token ohne `sub` werden von flownavigator, qaaudit, versteigerung beim Dekodieren akzeptiert | abgelehnt, wo jede Ausstellungsstelle `sub` setzt; audit_designer (Capability-Token ohne `sub`) und flowlib bleiben ohne `sub`-Pflicht | Pflicht-Claim sub | nein |
| D4 | Defekte oder unbekannte gespeicherte Hashes: ValueError, UnknownHashError oder Rust-Panic (bcrypt 4.x); nur qaaudit/versteigerung lieferten `False` | `False`, nach einer Blindprüfung gleicher Kosten | Kein HTTP 500, kein Zeitunterschied „Konto fehlt“ | nein |
| D5 | NUL im Passwort: passlib-Apps werfen beim Hashen und Prüfen `PasswordValueError` | Profil `bcrypt-passlib` lehnt beim Hashen mit `PasswordPolicyError` ab; Prüfen liefert `True`/`False` | Einheitliches Prüfen | nein |
| D6 | `extra_claims`/`data` können `exp`, `iat` (qaaudit, versteigerung auch `sub`, `type`) überschreiben; audit-portal verwirft ein `sub` in `extra_claims` still | `ValueError` beim Ausstellen | Reservierte Claims setzt nur die Bibliothek | nein – kein Aufrufer tut das |
| D7 | Prüfen folgt der Systemuhr der JWT-Bibliothek | eigene, injizierbare Uhr (`clock`); `exp <= jetzt − leeway` ist abgelaufen (Semantik von PyJWT) | Deterministische Tests, konfigurierbarer Leeway | nein |

Unverändert übernommen: Hash-Formate (`$2b$12$`, `$argon2id$v=19$m=65536,t=3,p=4`),
die Kürzung von bcrypt-Passwörtern auf 72 Byte (jetzt ausdrücklich, damit auch
bcrypt 5 funktioniert), HS256, Claim-Reihenfolge und -Werte, ganzzahlige
Zeitstempel (Mikrosekunden abgeschnitten), Standardlaufzeiten, Ablehnung von
`sub`/`jti` als Zahl, Ablehnung eines Refresh-Tokens als Zugangstoken
(regulierung), iat-in-der-Zukunft-Verhalten je App.
