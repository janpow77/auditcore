# Consumer-Anbindung

Stand 23.09.2026. Die Requirements der Anwendungen werden erst nach dem
zentralen Release v0.3.0 umgestellt (SHA256-gebundene Direktreferenzen wie bei
v0.2.0). Die folgenden Umstellungen wurden in **lokalen Kopien** der
Anwendungen auf den gebundenen Commits vorgenommen (je ein lokaler Branch
`consumer/auditcore-registry-sources`, nicht gepusht) und mit den gebauten
Wheels in isolierten Umgebungen geprüft. Keine Produktionsdatenbank, keine
Pushes in Consumer-Repositories.

| Consumer | Stelle | Umstellung | Tests vorher → nachher |
|---|---|---|---|
| audit_designer `1254591` | `backend/app/core/shared/research/register/sanctions.py`: `normalisiere_name`, `klassifiziere`, `_beruecksichtige_geburtsdatum_und_land`, `Listenindex` | Profil `audit_designer.sanctions` 2026.09.2 bzw. `audit_designer.sanctions_screening` 2026.09.1; `Listenindex.suche` nutzt `screening.ListIndex` und bildet `Sanktionstreffer` daraus | `tests/ecohesion/register/test_sanctions.py` 35 → 35 PASS; ECOHESION-Register und Recherche 341 → 341 PASS (2 Fehlschläge vorher wie nachher: fehlendes `celery` in der Testumgebung) |
| flowworkshop `3d1cb40` | `auditworkshop/backend/services/sanctions_service.py`: `normalize_name`, `_adjust_score_for_dob_country`, `SanctionsListIndex.search` | Profil `flowworkshop.sanctions_screening` 2026.09.1; Index je Liste aus der Bibliothek | `test_sanctions_multi`, `test_entity_matching_bibliothek`, `test_sanctions_db_storage` 29 → 29 PASS (davon 7 gegen Wegwerf-PostgreSQL 15 mit pgvector) |
| flowinvoice `fb2d185` | `backend/app/services/fraud_detection/sanctions_downloader.py` (`_parse_eu_fsf`, `_parse_ofac_sdn`, `_parse_un_sc`, `_parse_date_safe`), `pep_checker.py` (`_normalize_name`, `_match_name`) | XML über `sanctions_xml.parse_xml_list(..., dates="legacy")` (defusedxml), PEP über Profile `flowinvoice.pep`/`flowinvoice.pep_bulk` | `test_pep_checker`, `test_pipeline_profiles`, `pipeline/test_context` 47 → 47 PASS; 32/32 aufgezeichnete Originalfälle gegen die umgestellte Kopie gleich |

## Umstellungsanleitung

1. Requirements nach Release v0.3.0:
   `auditcore_entity_matching[fuzzy]==0.2.0` und
   `auditcore_registry_sources[fuzzy]==0.1.0` (Designer, flowworkshop) bzw.
   `auditcore_registry_sources[xml]==0.1.0` (flowinvoice), jeweils als
   SHA256-gebundene Direktreferenz auf die Release-Assets. Debian:
   `python3-auditcore-registry-sources` (`Depends` auf
   `python3-auditcore-harvest`, `python3-auditcore-entity-matching`;
   `python3-defusedxml` bzw. `python3-bs4` für die Extras; rapidfuzz ≥ 3.10.1
   hat kein passendes Bookworm-Paket und bleibt ein pip-Extra).
2. Designer:
   ```python
   from auditcore_entity_matching import classify, load_profile as lade_norm, normalize
   from auditcore_registry_sources import load_profile
   from auditcore_registry_sources.screening import ListIndex, ScreeningSettings, adjust_score

   _NORMALISIERUNG = lade_norm("audit_designer.sanctions", "2026.09.2")
   _ABGLEICH = ScreeningSettings.from_profile(
       load_profile("audit_designer.sanctions_screening", "2026.09.1")
   )
   ```
   `normalisiere_name` → `normalize(text, _NORMALISIERUNG)`, `klassifiziere`
   → `classify(wert, _NORMALISIERUNG, a, b)`, Geburtsjahr/Land →
   `adjust_score(...)[:3]`, `Listenindex` hält einen `ListIndex` über eine
   schmale Sicht (`entry_id`, `schema`, `name`, `aliases`, `birth_date`,
   `countries`) und bildet `Sanktionstreffer` aus `ScreeningHit`.
3. flowworkshop: wie 2 mit dem Profil `flowworkshop.sanctions_screening`;
   `normalize_name` → `legacy.flowworkshop_normalize_name_umschrift`; der Test
   `test_bibliothek_ist_gebunden` prüft danach die Versionen 0.2.0/0.1.0.
4. flowinvoice: Parser → `parse_xml_list(data, "<format>", dates="legacy")`,
   `_parse_date_safe` → `parse_date_legacy`, PEP → `legacy.flowinvoice_pep_normalize_name`
   und `bulk_screening.pep_score` mit `flowinvoice.pep_bulk`.
5. **Entschieden am 23.09.2026 (R10, „alle empfehlungen“):** Bei der Umstellung
   nach v0.3.0 werden die korrigierten Verträge eingesetzt: `screen()` mit
   `recommended_profile("sanctions_screening")` (Befund je Liste, Indikatoren),
   `company.check_vat`/`verify_company` mit `recommended_profile("company_verification")`
   in flowinvoice (heute gilt dort jede USt-IdNr. als ungültig, REG-C07),
   `MatchClient` statt der flowsearch-Clients (REG-C15; Schlüssel beschafft jeder
   Betreiber selbst, A3), PEP über `recommended_profile("pep_bulk")` (R3),
   Harvest-Adapter statt der eigenen Downloads (REG-C16; kein Auslisten bei
   fehlerhaften Zeilen, R8). Diese Umstellung ändert Ergebnisse gewollt.
6. **Entschieden am 23.09.2026 (R9):** Der Werkzeugeintrag `sanctions-screening`
   in audit_designer (`app/core/shared/research/registry.py`, `methodology_de`/
   `methodology_en`) wird korrigiert: kein „phonetische … Varianten“, sondern
   „unscharfer Namensabgleich (Token-Set) über Namen und Aliase“.

## Nicht angebunden (geplant)

- flowsearch `api/screening.py`, `recherche_orchestrator.py`: die Clients
  liefern heute nie Treffer; eine Umstellung auf `MatchClient` braucht einen
  OpenSanctions-Schlüssel und die Lizenzklärung (CC BY-NC 4.0) — NOT_CONFIGURED.
- osint `werkzeuge/traeger_quellen.py`: Adapter ZER/IHK/HWK liegen vor und sind
  live geprüft; die Anbindung (Skript → Harvest-Lauf) ist geplant.
- flowinvoice `CompanyVerifier`: korrigierte VIES-/Registerprüfung verfügbar,
  Umstellung ist eine fachliche Entscheidung (siehe 5).
