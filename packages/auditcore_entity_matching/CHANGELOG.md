# Changelog auditcore_entity_matching

## 0.2.3 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pflichtabhängigkeit `auditcore_common==0.1.1`; README nach der Vorlage.

## 0.2.2 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`).

- `fingerprint` → `auditcore_common.hashing.canonical_sha256`,
  `available_profiles` → `profiles.packaged_profile_ids`,
  `load_profile` → `profiles.load_packaged_profile(require_text=True,
  invalid_name="missing")`, `recommended_profile` →
  `profiles.recommended_profile_id`, `_rapidfuzz` →
  `optional.require_module`. Öffentliche Namen, Meldungen und Fehlerklassen
  bleiben; die Gleichheit ist in `auditcore_common` differenziell belegt und
  hier durch die unveränderten Replay-/Vertragstests.

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 989 bestehenden Tests (Replays gegen die
aufgezeichneten Originalausgaben von flowworkshop, audit_designer, flowinvoice,
audit-portal und riskanalysis, Vertrags-, Entscheidungs- und
Architekturtests) laufen unverändert grün; Profildaten und Fingerprints sind
bytegleich.

- `normalize` je Algorithmus zerlegt (`_nfkd_lower_regex`,
  `_lower_nfkd_ascii`, `_translate_then_casefold`, `_casefold_fold_nfkd`)
  mit gemeinsamen Schritten `_apply_fold_map`, `_strip_combining` und
  `_drop_tokens`; die Auswahl steht als Tabelle, unbekannte Algorithmen
  fallen wie bisher auf die Casefold-Variante.
- `profile_from_dict` je Abschnitt zerlegt (`_normalization`,
  `_classification`, `_resolution`); Prüfreihenfolge und Fehlermeldungen
  unverändert.
- `Any` nur noch an der Grenze zum rohen Profil-JSON (`_RawDocument`) und
  im öffentlichen Feld `Profile.source`; `fingerprint`, `_strings` und
  `_mapping` nehmen `object`, `_rapidfuzz` liefert `ModuleType`.

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 2 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Vorkommen (Gate-Zählung) | 7 | 2 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. `auditcore_risk` pinnt die neue
Version (`auditcore_entity_matching==0.2.2`).
