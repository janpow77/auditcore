# Changelog – auditcore_auth

## 0.1.0 – 2026-09-25

- Passwort-Hashing mit den Profilen `bcrypt`, `bcrypt-passlib` und `argon2id`;
  Verifikation aller gespeicherten bcrypt- und argon2-Formate unabhängig vom
  Profil, Rehash-Signal (`check`, `verify_and_update`), strikte Formatprüfung vor
  dem Backend, Blindprüfung bei fehlendem Hash, 72-Byte-Regel auch unter bcrypt 5.
- JWT über PyJWT: Profile mit Algorithmus-Allowlist (kein `none`, keine
  HMAC/Public-Key-Mischung), Claim-Reihenfolge, festen Claims, Pflicht-Claims
  (`exp` immer), Leeway, Tokentypen, Schlüssel- und Tokenlängen; injizierbare,
  zeitzonenbewusste Uhr.
- Kompatibilitätsprofile für neun Anwendungen (byteweise identische Token,
  alle bisherigen Token und Hashes gültig); Charakterisierung mit 19
  ausgestellten Token, 153 Prüffällen und 90 Passwortfällen der Originale.
- Extra `fastapi`: Bearer-Dependency mit 401 und `WWW-Authenticate` nach RFC 6750.
- `constant_time_equals` für Geheimnisvergleiche.
