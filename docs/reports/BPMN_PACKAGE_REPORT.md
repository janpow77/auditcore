# auditcore_bpmn 0.1.0 – Paketbericht

Stand 25.09.2026. Quelle: `janpow77/audit_designer@eff41a4c` (FlowStat-BPMN,
Blob-geprüft, `provenance.json`), Rechtstexte VO (EU) 2021/1060, Delegierte
VO (EU) Nr. 480/2014, VO (EU) Nr. 1303/2013 (Cellar-Abruf, SHA-256 in
`tools/build_profiles.py`). Rechte: `USER_AUTHORIZED_MIT` (22.09.2026).

## Umfang

Gehärtetes Parsen (defusedxml bzw. Expat ohne DTD/Entitäten/externe
Verweise), rundlauftreues Schreiben, Elementmodell aller BPMN-2.0-Elemente,
FlowAudit-Schema 1.0/1.1 (`docs/bpmn/flowaudit-schema-1.1.md`, XSD), Profile
je Förderperiode, Prüfregeln (Struktur, fachlich, Prüfbehörden-Funktionen,
Funktionstrennung, Sammlung; de/en), Diagrammsammlung mit Speicher-Port,
Freigaben mit SHA-256, Versions- und Soll/Ist-Vergleich, Neutralisieren,
Anreichern von Altbeständen, Berichte (Prozesstabelle, RCM,
Feststellungsliste, Durchlauftest, KA-Kategorievorschlag), Vorlagen
(synthetisch), legacy-treue Kennzahlen/BVA-Validierung/Excel-/PDF-Bericht.

## Nachweise (lokal ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| `pytest tests` (Python 3.12) | 545 bestanden, 1 übersprungen (lokale Nutzerdiagramme) |
| Charakterisierung gegen Originale (95 Fälle, pandas 2.1.4) | eine dokumentierte Abweichung (DOCTYPE), sonst gleich inkl. Excel-Zellen/-Format und PDF-Bytes |
| lokal: 54 Nutzerdiagramme (`AUDITCORE_BPMN_LOCAL_FIXTURES`, nicht im Repo) | 54 bestanden (Lesen, Rundlauf, Regeln, Kennzahlen, Vorschläge, Neutralisieren ohne E-Mail-Reste) |
| `ruff check` (inkl. C901 ≤ 10), `mypy --strict src`, `bandit -ll` | PASS |
| `auditcore-bibquality --strict` | REVIEW_REQUIRED (Policy/Supply-Chain/OSS-Prüfung wie bei den übrigen Paketen), keine FAIL |
| `scripts/verify_domain_packages.py … --apt` (Debian bookworm, ohne Netz) | PASS: Wheel, pip-Index, Hash-Installation, Selektivinstallation, `.deb` Revision 1→2, signierte APT-Quelle, Installieren/Upgrade/Entfernen |

## Offene Punkte

- Bewertungskriterien (BK) sind in keinem Rechtstext enthalten; die
  Anwendung speist sie ein (`Profile.with_assessment_criteria`).
- Vorlagen sind synthetisch; die Nutzerdiagramme sind nicht anonymisiert
  und werden erst nach erneuter Freigabe verwendet.
- `auditcore_documents` (Textsynopse) und `auditcore_sampling`
  (Stichprobenumfang des Kontrolltests) sind noch nicht angebunden.
- Profil 2028–2034 fehlt (Rechtsgrundlage noch nicht erlassen).
