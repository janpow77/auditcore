# Changelog – auditcore_privacy

Alle wesentlichen Änderungen dieses Pakets werden in dieser Datei dokumentiert.

## 0.1.0 (2026-10-01)

### Neu
- Erstveröffentlichung von `auditcore_privacy` als eigenständige Fachbibliothek im auditcore-Monorepo.
- Deterministische und kollisionsfreie Pseudonymisierung für Personen, Organisationen und strukturierte Prüfdaten:
  - Feste Bindung an Mandanten- oder Fall-Scopes (`scope_key`, kryptografischer Salt).
  - Deterministische Wiederholung: Gleicher Klartext im selben Scope liefert stets dasselbe Pseudonym.
  - Kollisionsfreiheit: Unterschiedliche Klartexte im selben Scope führen nie zur selben Ersetzung; automatische Streuwertauflösung (Versuche 0..63) und deterministische Reservekennzeichnung.
  - Schutz: Klartexte werden nie als Nachschlageschlüssel abgelegt, sondern als Einweg-Streuwert (`original_hash` über Blake2b).
- Drei Ersetzungsarten:
  - `PSEUDONYM`: Natürlich wirkende Namen für Personen (unter Erhalt der Wortzahl) und Firmen (unter Erhalt der Rechtsform).
  - `FORMATTREU`: Synthetische, aber prüfzifferngültige Ersatzwerte (IBAN nach ISO 13616 mit Null-Bankleitzahl, E-Mail unter `.example` nach RFC 2606, Telefonnummern im reservierten Prüfbereich).
  - `PLATZHALTER`: Nummerierte Schutzmarken (`[Anschrift 1]`, `[Konto 1]`, `[Aktenzeichen 1]`, `[Steuernummer 1]`, `[USt-IdNr 1]`).
- Fundstellenmaskierung (`mask_text`): Sichere Kürzung und Überdeckung mit Schutzpunkten (`•`), damit Ergebnislisten keine sensiblen Rohdaten exponieren.
- Trennung von Schlüssel, Zuordnungstabelle und Fachdaten (`PseudonymMapping`, `MappingStore`).
- Ausdrückliche Klarstellung: Pseudonymisierung schützt Daten bei der Prüfung, stellt jedoch keine unwiderrufliche Anonymisierung dar.
