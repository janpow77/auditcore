# auditcore_legal_sources

Eigenständig installierbare Quellenfamilie für Rechts-, Parlaments- und
Prüfquellen: **Bundestag DIP** (Drucksachen) und **EUR-Lex/Cellar** (SPARQL).
Das Paket enthält Anfrageaufbau, strikte Antwortprüfung, Normalisierung zu
`LegalDocument` (stabile Identität, Contenthash, geparstes Publikationsdatum,
Provenienz) sowie versionierte Quellprofile. Abruf, Seitenfolge,
Wiederholungen, Rate-Limits, Checkpoints und Senken übernimmt der gemeinsame
Kern `auditcore_harvest`; Scheduler, Datenbank und Rechte bleiben beim Consumer.

```python
from auditcore_legal_sources import dip
from auditcore_legal_sources.profile import load_profile

profil = load_profile("auditdatabase.esi", "2026.09.1")
params = dip.drucksache_query(profil, "EFRE")          # enthält keinen API-Schlüssel
seite = dip.parse_page(antwort_json)                    # ParseError statt leerem Erfolg
dokumente, fehler = dip.normalize_page(seite, profil)
```

Profile: `auditdatabase.esi` und `audit_designer.vp_ai` (je 2026.09.1) –
aus den ausgeführten Quellanwendungen aufgezeichnet und bewusst getrennt.
`legacy` reproduziert beide Anwendungen exakt; die Korrekturen (u. a. nie
geparste Datumswerte, API-Schlüssel im Code, verdeckte Teilfehler) stehen in
[docs/behavior-changes.md](docs/behavior-changes.md).

Zugangsdaten: Der DIP-API-Schlüssel kommt ausschließlich aus dem
Credential-Provider des Consumers; ohne Schlüssel ist die Quelle NOT_CONFIGURED.
Abgerufene Inhalte unterliegen den Nutzungsbedingungen der Quellen und sind
nicht Teil des Pakets. Lizenz: MIT (siehe `NOTICE`).

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Debian-Paket: `python3-auditcore-legal-sources`.
