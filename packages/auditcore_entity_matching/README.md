# auditcore_entity_matching

Eigenständig installierbare Bibliothek für **nachvollziehbare
Entitätsnormalisierung, LEI-Prüfung und Abgleichkomponenten**. Kern ohne
Laufzeitabhängigkeiten; unscharfe Vergleiche über das Extra `[fuzzy]`
(rapidfuzz). Keine Datenbank, kein ORM, keine Schwellen als stille Vorgabe.

```python
from auditcore_entity_matching import check_lei, load_profile, normalize

assert check_lei("529900T8BM49AURSDO55").valid
assert not check_lei("7LTWFZYICNSX8D621K87").valid        # Prüfziffern falsch
profil = load_profile("flowworkshop.state_aid", "2026.09.1")
assert normalize("Brüder Weiß GmbH & Co. KG", profil) == "brueder weiss"
```

| Modul | Inhalt |
|---|---|
| `profiles` | Versionierte, quellengebundene Profile mit Fingerprint: `flowworkshop.state_aid`, `flowworkshop.sanctions`, `audit_designer.sanctions`, `flowworkshop.entity_resolution`, seit 0.2.0 `riskanalysis.payee` (Rechnungssteller-Normalisierung der Red-Flag-Regel RF09). |
| `normalize` | Vergleichsform nach genau einem Profil. Varianten bleiben getrennt. Empfohlen für neue Consumer (Entscheidung 23.09.2026): `flowworkshop.state_aid` mit ä → ae, ö → oe, ü → ue, ß → ss. |
| `lei` | Formatprüfung, Prüfziffern ISO 7064 MOD 97-10, Extraktion aus Freitext. |
| `matching` | `best_match` mit Einzelwerten je Scorer und Profilidentität; `classify` für Screening-Klassen; `pair_score` für den Vergleich zweier bereits normalisierter Namen mit ausdrücklich benanntem Scorer. Benötigt `[fuzzy]`. |
| `legacy` | Verhaltensgleiche Funktionen der Quellanwendungen. |

Herkunft: `flowworkshop@a05bb21`, `audit_designer@030a71e`, `riskanalysis@b5c523b` (seit 0.2.0); MIT-Freigabe für den
extrahierten Bibliothekscode (siehe `NOTICE`, `provenance.json`). Unterschiede
zum Original und offene fachliche Entscheidungen:
[docs/behavior-changes.md](docs/behavior-changes.md). Debian-Paket:
`python3-auditcore-entity-matching`.
