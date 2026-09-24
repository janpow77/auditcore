# auditcore_invoicesynth 0.1.0 — Bericht

Stand: 24. September 2026. Etappe E1 der Donut-Umsetzung
(`docs/architecture/DONUT_OCR_PLAN.md` 2b/2d; Entscheidungen E1–E9 vom
24.09.2026, Zitat „Donut alle Empfehlungen“). Nicht veröffentlicht.

| Punkt | Stand |
|---|---|
| Paket/Version | `auditcore_invoicesynth` 0.1.0 (neue Distribution, E1) |
| Herkunft | Neuimplementierung in auditcore, keine Quellbindung (`EXPECTED_SOURCES`: leere Menge); kein Donut-Code übernommen; Basisdaten aus `auditcore_invoicegenerator` 0.2.0 (unverändert) |
| Lizenz | MIT; Freigabe des Rechteinhabers vom 22.09.2026 („die Bibliotheken sollen MIT sein …“); Schriften nicht verteilt (DejaVu: Bitstream Vera, Liberation/Noto: OFL-1.1) |
| Abhängigkeiten | Kern: `auditcore_invoicegenerator==0.2.0`; Extra `render`: Pillow ≥ 9.4 (Debian `python3-pil`) |
| Funktionen | Anreicherung (fiktive prüfziffer-gültige IBAN/BIC, USt-IdNr./UID, Steuerschemata DE/AT, Fehlerfälle), 10 Vorlagen (2 nur Holdout), Beschriftungs-Synonyme, Zahlen-/Datumsformate, freie Schriften mit SHA-256, Scanrauschen, Donut-Ausgabe mit Manifest und Datensatz-Hash, Ziel-JSON `auditcore_invoice_v1` (E8), Bewertung mit Schwellen E6, CLI |

## Nachweise

| Prüfung | Ergebnis |
|---|---|
| pytest | 61 passed (Kennungen, Formate, Schema/Tokenfolge, Anreicherung, Plan/Holdout, alle Vorlagen, Scanrauschen, Datensatz-Hash, Manipulationserkennung, Schriften, Bewertung, CLI, Architektur, Provenienz) |
| ruff, mypy --strict (src + tests), bandit -ll | PASS |
| auditcore-quality strict (Framework `verwaltung-app-framework@4f9e81b`) | Syntax, Lint, Typen, bandit, Tests PASS; AC-DEP-001 FAIL nur wegen `ecdsa` in der Plattform-Entwicklungsumgebung (nicht Teil des Pakets; `pip-audit` in sauberer Umgebung mit Paket + Pillow ohne Befund); Policy/Supply-Chain REVIEW_REQUIRED (Release-Nachweise folgen mit dem Release) |
| Pilot 2 000 Belege (Seed 42, Standardkonfiguration) | zwei unabhängige, parallel laufende Erzeugungen: identischer Datensatz-Hash `192e329e531ba16028c314f36007737637fdaaf59e0eb66095fb84a4056174f3`; 2 223 Bilder (train 1 795, validation 165, test_synthetic 163, test_layout_holdout 100), 713 MB, ≈ 16,5 min je Lauf auf der NUC (CPU); `verify` PASS |
| Sichtprüfung | 16 Zufallsbelege: Überlappung langer Beschriftungen mit Werten gefunden und behoben (`_pair`), danach 32 weitere Zufallsbelege ohne Befund (Plan verlangt 50: **teilweise**, 48 insgesamt gesichtet) |
| pip/APT (lokal) | `verify_domain_packages.py` für dummygenerator, invoicegenerator, invoicesynth mit `--apt`: PASS (Build, Hash-Install, Rauchtest, Selektivinstallation, zwei Debian-Revisionen, signierte APT-Quelle, Install/Upgrade/Remove) |

Laufzeitumgebung des Piloten: Pillow 12.3.0, Schriften DejaVu, Liberation, Noto
(Hashes im Manifest). Ein anderer Rechner mit anderer Pillow-/zlib-/Schriftversion
erzeugt einen anderen, aber in sich reproduzierbaren Hash.

## Consumer

Erster Consumer ist das Trainingswerkzeug (Etappe E3, `auditcore_invoicesynth.train`)
sowie die Testbelege von `auditcore_documents` 0.2.0
(`tools/build_donut_fixtures.py`). Eine Anwendung bindet das Paket nicht ein.

## Offen

- Sichtprüfung auf 50 Belege vervollständigen (48 gesichtet).
- Stempel können gedruckte Felder teilweise verdecken (gewollt realistisch;
  Ziel-JSON enthält den gedruckten Wert) – bei der Bewertung auf T1 beobachten.
- Katalogtrennung Firmen-/Positionsnamen für Testsätze (Plan, Risiko
  „Überanpassung“) noch nicht umgesetzt.
