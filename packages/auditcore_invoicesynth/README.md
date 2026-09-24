# auditcore_invoicesynth

Synthetische Trainings- und Testdaten für eine Donut-basierte Belegerkennung
deutscher und österreichischer Rechnungen (Plan
`docs/architecture/DONUT_OCR_PLAN.md`, Abschnitte 2b und 2d; Entscheidungen
E1–E9 vom 24.09.2026). Grundlage sind die Datensätze aus
`auditcore_invoicegenerator` 0.2.0, der unverändert bleibt.

```bash
pip install 'auditcore_invoicesynth[render]==0.1.0'
auditcore-invoicesynth fonts                       # freie Systemschriften + SHA-256
auditcore-invoicesynth plan  --seed 42             # Plan ohne Bilder
auditcore-invoicesynth build --seed 42 --out ds/   # Pilot: 2 000 Belege
auditcore-invoicesynth verify ds/                  # Dateien + Datensatz-Hash prüfen
auditcore-invoicesynth evaluate ds/ --split test_layout_holdout --predictions p.jsonl
```

## Inhalt

| Baustein | Umfang |
|---|---|
| Anreicherung (`enrich`) | fiktive IBAN/BIC (BLZ-Liste mit führender 9 bzw. `99xxx`, BIC `SYNT…`), USt-IdNr. DE (ISO 7064 MOD 11,10) und UID AT mit gültiger Prüfziffer, Steuernummer, Steuerzeilen 19/7/gemischt, § 19 UStG, Reverse Charge, AT 20/13/10/gemischt; Beträge mit `Decimal`, `netto + USt = brutto` exakt; Fehlerfälle `wrong_total`, `missing_vat_id`, `missing_iban` |
| Vorlagen (`layouts`) | 10 Vorlagen: `kopf_links`, `kopf_rechts`, `summen_unten`, `fusszeile_bank`, `zweispaltig`, `kleinunternehmer`, `gutschrift`, `mehrseitig` (Training) und `holdout_kompakt`, `holdout_briefkopf` (nur Testsatz `test_layout_holdout`) |
| Beschriftungen/Formate | Synonymlisten je Feld (DE, ≈ 10 % EN); `1.234,56`, `1234,56`, `1 234,56`, `1,234.56`; Währung vor/nach dem Betrag (`EUR`/`€`) oder ohne; `15.01.2026`, `15.1.26`, `15. Januar 2026` (AT: Jänner), ISO, englisch |
| Schriften (`fonts`) | nur Katalog freier Familien (DejaVu, Liberation, Noto); **nicht eingebettet**: Systemschriften oder `fetch_font` mit SHA-256; optionale Prüfsummen-Pins; Holdout-Schrift standardmäßig `DejaVu Serif` |
| Scanrauschen (`augment`) | Drehung ±3°, Perspektive, Unschärfe, JPEG, Salz-und-Pfeffer, Graustufe/Binarisierung, Stempel, Kugelschreiber, Lochung, Faltkante, 150–300 dpi; alles aus dem Einzelseed |
| Ausgabe (`dataset`) | Donut-Format `split/metadata.jsonl` (`file_name`, `ground_truth` = `{"gt_parse", "meta"}`), `manifest.json` mit Versionen, Konfiguration, Schriften, SHA-256 je Datei und Datensatz-Hash |
| Ziel-JSON (`schema`) | `auditcore_invoice_v1`, nur Kopf-/Summenfelder (E8); Werte = das **Gedruckte**; Donut-Tokenfolge mit Task-Token `<s_auditcore_invoice_v1>` und Rücklesung |
| Bewertung (`evaluation`) | Feldgenauigkeit, Falsch-/Fehlt-/Halluzinationsquote, Belegquote, Falschwert-Quote nach Plausibilität, Abnahmeschwellen E6 |

**Reproduzierbarkeit:** Datensatz-Hash = SHA-256 über die sortierten Zeilen
`Pfad<TAB>SHA-256` aller Dateien außer dem Manifest. Gleicher Seed, gleiche
Konfiguration, gleiche Schriftdateien und gleiche Pillow-/zlib-Version ergeben
denselben Hash (Test `test_same_seed_same_hash_different_seed_different_hash`).
Das Manifest enthält keine Zeitstempel.

**Kennzeichnung:** Jede Seite trägt oben „SYNTHETISCH – kein echter Beleg,
Kennungen fiktiv“ und unten „SYNTHETISCHE TRAININGSDATEN – nicht zahlen, keine
Steuerwirkung“; der Builder bricht ab, wenn eine Seite ohne beide Vermerke
entstünde. Prüfziffer-gültige Kennungen können zufällig realen Nummern
entsprechen (Entscheidung E5).

Kern ohne Zusatzpakete (Plan, Anreicherung, Ziel-JSON, Manifestprüfung,
Bewertung). Extra `render`: Pillow ≥ 9.4 (Debian: `python3-pil`).

Herkunft und Lizenz: `NOTICE`, `provenance.json` (MIT, Freigabe des
Rechteinhabers vom 22.09.2026; Neuimplementierung ohne Quellrepository).
Debian-Paket: `python3-auditcore-invoicesynth`.
