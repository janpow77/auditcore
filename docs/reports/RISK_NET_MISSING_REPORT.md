# auditcore_risk 0.3.0 – fehlender Nettobetrag als „unbestimmt“

Stand: 24.09.2026. Anlass: riskanalysis PR #1 bricht mit der echten MDB
(`t_Auswertung_Gesamt`, nur Bruttobeträge) ab. Nutzerklarstellung vom
24.09.2026: Nettodaten sollen „nur im Code vorgesehen sein“ – die Auswertung
darf nicht auf echte Nettodaten warten; Entscheidung K2 (netto, kein Rückfall
auf brutto) bleibt.

## Befund in 0.2.0

| Fall | `riskanalysis.year_bound 2026.09.4` |
|---|---|
| Spalte `nettobetrag` fehlt | `InputError` (`when_missing_columns: "error"`) – Abbruch |
| Wert leer (`NaN`/`None`/`pd.NA`) | Ersatzbetrag `missing_value: 0.0` → RF02/RF08 still „kein Merkmal“ |

Eine leere Nettospalte im Consumer hätte also falsche Entwarnungen erzeugt; ein
Profil konnte das nicht ausdrücken (`missing_value` musste eine Zahl sein).

## Änderung

* Regelarten `near_threshold` und `missing_procurement`: optionaler Parameter
  `missing_amount_reason` (verlangt `missing_value: null`). Leerer Betrag →
  `None` (unbestimmt) mit dieser Begründung. `missing_procurement` bleibt
  `False`, wo der Betrag nicht entscheidet (echte Vergabekennung oder nicht
  vergaberelevante Kostenart).
* `when_missing_columns: "undetermined"`: fehlende Betragsspalte wie leere
  Werte; nur für diese beiden Regelarten mit `missing_amount_reason` und nur,
  wenn die Betragsspalte die einzige Pflichtspalte ist (beim Laden geprüft).
* Profil `riskanalysis.year_bound 2026.09.5` (`APPROVED`, abgeleitet von
  2026.09.4, Entscheidungskennung K2a): RF02 und RF08 mit „Nettobetrag fehlt in
  der Quelle“. Mit Nettobetrag identisch zu 2026.09.4 (Test).
* Alle bisherigen Profilfassungen bleiben bytegleich: `tools/build_profiles.py`
  erzeugt sie unverändert, die Replay-Tests laufen unverändert.

## Weitere Profile geprüft

| Profil | Befund |
|---|---|
| `flowinvoice.risk_checker` (fb2d18568d2e, 2026.09.2, 2026.09.3) | `net_amount` ohne Ersatzwert: `None` → `InputError` (laut, wie die Quelle; `net_amount` ist dort Pflichtfeld). Keine neue Fassung nötig. |
| `flowinvoice.rbvk_wibank`, `exante_*` | keine Nettobeträge (`projekt_budget`, Quoten, Zähler) |
| `audit_designer.flowstat_belegliste` | `projektbetrag` mit `skip`/0.0 – Legacy, kein Nettobezug |
| `riskanalysis.year_bound` 2026.09.2–2026.09.4 | betroffen, abgelöst durch 2026.09.5 |

## Nachweise

| Prüfung | Ergebnis |
|---|---|
| `pytest` (packages/auditcore_risk) | 2375 passed (davon 7 neu in `test_missing_net.py`) |
| `ruff check`, `ruff format --check`, `mypy src`, `bandit -ll` | ohne Befund |
| `tests/installed_smoke.py` | PASS (14 Profile, RF02 unbestimmt ohne Nettospalte) |
| `verify_domain_packages.py --apt` (harvest, entity_matching, procurement, statistics, risk) | 49/49 PASS; Wheel `auditcore_risk-0.3.0` SHA-256 `a0bf4d6a47cfc4e52169082dd9bbf521732685f2c1832f610e219b7ae4d4f19b` (lokaler Build) |
| Consumer-Vorabtest riskanalysis (Kopie, echte MDB, nur Aggregate) | 93.444 Belege; RF02 93.444 unbestimmt; RF08 38.465 unbestimmt, übrige „kein Merkmal“; RF01 2.208, RF09 2.863, RF10 4.312, RF11 9.880, RF12 11.121 Treffer |

Release (v0.3.2, signiert) und Consumer-Umstellung erfolgen getrennt.
