# Profile

Ein Profil ist eine benannte Sammlung von Prüffunktionen. `strict` ist der
Standard. Die Legacy-Profile existieren, damit eine Anwendung auf die
Bibliothek umgestellt werden kann, **ohne dass sich Ergebnisse ändern**; der
Wechsel auf `strict` ist danach eine bewusste, eigene fachliche Entscheidung
(Differenzen: [`differences.md`](differences.md)). Jedes Legacy-Profil ist
durch ausgeführte Originalaufrufe belegt (`tests/test_replay.py`).

| Profil | Arten | Herkunft |
|---|---|---|
| `strict` | iban, bic, vat_id, tax_id, tax_number, lei, register_number | Neuimplementierung |
| `flowinvoice.legacy` | iban, bic, vat_id, tax_number | flowinvoice `services/validators.py` |
| `audit_portal.legacy` | wie oben | audit-portal `services/validators.py` (Blob-gleich) |
| `flowinvoice.pipeline.legacy` | iban, vat_id | flowinvoice `pipeline/stages/validation.py` |
| `audit_portal.pipeline.legacy` | iban, vat_id | audit-portal, gleicher Regelteil |
| `documents.donut` | iban, vat_id | auditcore_documents Donut-Stufe |
| `invoicesynth.legacy` | iban, vat_id | auditcore_invoicesynth `identifiers.py` |
| `flowworkshop.legacy` | lei | flowworkshop `entity_resolution.py` |

Zusätzlich bildet `legacy_flowinvoice` die Einzelfunktionen
`validate_german_vat_id`, `validate_uk_vat_id` und `normalize_vat_id`
(`RiskChecker._normalize_vat_id`) nach, `legacy_pipeline` die Funktion
`flowworkshop_extract_lei_from_text`.

## `flowinvoice.legacy` / `audit_portal.legacy`

**Warum:** flowinvoice meldet Rechnungsmerkmale mit `ValidationResult`
(Status und deutsche Meldung) an Oberfläche und Regelwerk. Eine strengere
Prüfung würde bisher „gültige“ Rechnungen plötzlich als fehlerhaft melden.
audit-portal ist ein Fork; die Datei ist byte-identisch (Blob `d3c09fbd`).

Beobachtetes Verhalten (übernommen):

- **IBAN ohne Modulo-97-Prüfung.** Nur Muster `^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$`
  und Länge für zehn Länder (DE, AT, CH, FR, IT, ES, NL, BE, PL, GB); jede
  andere Länge anderer Länder ist gültig, ebenso Ländercodes wie `XX`.
  599 von 2 919 Stichproben sind im Original gültig, haben aber eine falsche
  Prüfziffer.
- Normalisierung nur `strip()`, `upper()` und Entfernen von Leerzeichen;
  Bindestriche, geschützte Leerzeichen oder das Präfix `IBAN` machen die
  IBAN ungültig.
- `\d` akzeptiert auch nicht-lateinische Ziffern (z. B. arabisch-indische).
- USt-IdNr.: 27 Muster ohne Prüfziffer; Belgien auch 9-stellig; keine `XI`;
  `country_code` muss exakt (Großschreibung) einem Schlüssel entsprechen.
- BIC: Institutskennung nur Buchstaben, kein Ländercode-Abgleich (`DEUTXXFF` gültig).
- Steuernummer: fünf Formatmuster; 13-stellige Bundessteuernummern sind ungültig.
- Rückgabewert bei Erfolg: normalisierter Wert, bei Fehler der Rohwert.
- Einzige Abweichung: Eingaben, die weder Zeichenkette noch „falsy“ sind,
  lösten `AttributeError` aus; das Profil liefert `INVALID` (`invalid_type`).

## `flowinvoice.pipeline.legacy` / `audit_portal.pipeline.legacy`

**Warum:** Die Validierungsstufe der Dokumenten-Pipeline (`IbanChecksumRule`,
`VatIdFormatRule`) entscheidet über `REVIEW_NEEDED`/`REJECTED`. Sie lebt in
audit-portal weiter und wurde in `auditcore_documents` übernommen; ihre
Entscheidungen sind in bestehenden Läufen dokumentiert.

- IBAN: Länge 15–34, Länderlänge für neun Länder, Modulo 97 mit
  `ord(char) - 55` für jedes Nicht-Ziffern-Zeichen. Folge: `@` zählt als 9,
  `;` als 4 – `CZ650800000019200014539@` gilt als gültig. Englische Meldungen.
- USt-IdNr.: acht Länder; nur das Präfix wird großgeschrieben, das Muster
  auf den Rohwert angewandt (`de136695976` → ungültig); unbekanntes Land →
  `REVIEW` (hier `INVALID`/`unknown_country`), leer → übersprungen
  (hier `MISSING`). `details["outcome"]` und `details["severity"]` wie im Original.
- `None` führte zu `AttributeError`; hier `MISSING`.

## `documents.donut`

**Warum:** Die Donut-Stufe von `auditcore_documents` (Entscheidung E5,
24.09.2026) prüft bereits Prüfziffern DE/AT mit deutschen Meldungen. Das
Profil macht diese Regel für die Umstellung von `auditcore_documents` auf
diese Bibliothek verfügbar.

- Werte werden kompaktiert (Leerraum entfernt, Großschreibung), dann IBAN wie
  Pipeline und USt-IdNr. mit acht Mustern und Prüfziffer DE/AT.
- Leerer Wert: Die Stufe überspringt ihn vor dem Aufruf; hier `MISSING`.

## `invoicesynth.legacy`

**Warum:** Der Synthesegenerator nutzt `iban_valid`/`vat_id_valid` als
Plausibilitätsprüfung erzeugter Daten (nur DE/AT). Das Profil hält dieses
Verhalten für eine Umstellung fest; fachlich ist `strict` vorzuziehen.

- IBAN: Länge 15–34, Länderlänge nur DE/AT, Modulo 97; nicht-ASCII-Zeichen
  wie `²` oder `ä` lösten `ValueError` aus – hier `INVALID`.
- USt-IdNr.: nur DE (erste Ziffer ≠ 0) und ATU mit Prüfziffer; jedes andere
  Land ist ungültig.

## `flowworkshop.legacy`

**Warum:** Das Workshop-Entity-Resolution prüfte LEIs nur nach Format. In
`auditcore_entity_matching` ist diese Variante bereits als Legacy
(`flowworkshop_is_valid_lei`) erhalten; das Profil macht sie hier verfügbar.
flowworkshop selbst ist durch ecohesion abgelöst (keine Deploys mehr).

- LEI: `strip()`, `upper()`, Muster 18 alphanumerisch + 2 Ziffern, **keine
  Prüfziffernprüfung** (128 von 574 Stichproben mit falscher Prüfziffer gelten
  als gültig).

## Bewusste Festlegungen im Profil `strict`

- Nur ASCII: nicht-lateinische Ziffern, `ß`, Umlaute → `invalid_characters`
  (vor der Großschreibung geprüft, weil `"ß".upper() == "SS"`).
- Jeder Leerraum (auch geschütztes Leerzeichen, Tabulator, Zeilenumbruch)
  wird entfernt; Trennzeichen je Art: IBAN `-` und Präfix `IBAN`, USt-IdNr.
  `. - / \`, Steuer-ID/Steuernummer `/ - .`.
- DE-USt-IdNr. mit führender 0 ist ungültig (wie `auditcore_invoicesynth`).
- Belgische USt-IdNr. nur 10-stellig mit führender 0 oder 1 (VIES seit 2023).
- Steuer-ID: drei gleiche Ziffern direkt hintereinander sind unzulässig
  (Regel seit 2016); python-stdnum prüft das nicht.
- BIC: Institutskennung alphanumerisch (ISO 9362:2014), Länderliste ISO 3166-1.
