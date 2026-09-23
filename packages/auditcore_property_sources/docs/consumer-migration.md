# Consumer-Umstellung (geplant)

Status: **GEPLANT.** Nutzerentscheidung 2026-09-23: Das Paket wird auch ohne
bereits belegten Mehrfachnutzen gebaut – „der mehrfache Nutzen kommt noch“.
Heute hat jede Quelle genau einen Consumer. Die Anbindung per Requirements
erfolgt erst mit dem zentralen Release v0.3.0; bis dahin keine Änderung in
den Consumer-Repositories.

Getestete Integrationsvariante: `tools/consumer_integration.py` wendet die
unten stehenden Umstellungen auf **Kopien** beider Repositories an, installiert
nichts in die Repositories, startet die Original-Einstiegspunkte
(`hole_bestand`, `parse_detail`, `merge_address`) gegen das installierte Wheel
und vergleicht mit den aufgezeichneten Originalergebnissen. Ergebnis
2026-09-23: 8/8 PASS; die 10 bestehenden versteigerung-Tests laufen auf der
umgestellten Kopie unverändert grün.

## wohnungsmonitor (`janpow77/wohnungsmonitor`)

`requirements.txt` bzw. Installation: `auditcore_property_sources==0.1.0`
(ohne Extra – Paging und Netzwerk bleiben in den Exportern).

| Datei | bisher | neu |
|---|---|---|
| `immobilien_export.py` | `parse_page`, `normalise` | `parse_page = lambda doc: _ps.parse_page(doc)[0]`; `normalise(a) = _ps.normalise(a, plz_bezirke())` |
| `inberlinwohnen_export.py` | `total_count`, `learn_attributes`, `parse_page`, `normalise` | `_ps.total_count`, `_ps.parse_page`; `learn_attributes` aktualisiert `MERKMALE` aus `_ps.learn_attributes(doc, MERKMALE)`; `normalise(e) = _ps.normalise(e, MERKMALE)` |
| `kleinanzeigen_export.py` | `parse_page`, `brauchbar`, `normalise` | `_ps.parse_page`, `_ps.usable`; `normalise(roh) = _ps.normalise(roh, bezirke_laden())` |
| `bienici_export.py` | `normalise` | `_ps.normalise(a)` – Standard `"legacy"` wie bisher (PS-D03); `"minimal"` wählbar |
| `citya_export.py` | `katalog`, `gesamtzahl`, `ist_wohnraum`, `normalise` | `_ps.catalog`, `_ps.total`, `_ps.is_residential`, `_ps.normalise` |
| `paruvendu_export.py` | `_karten`, `normalise` | `_ps.cards`, `_ps.normalise` |

(`_ps` = das jeweilige Modul aus `auditcore_property_sources`.) Die Dateien
`plz_bezirke.json` und `ortsteile_bezirke.json` bleiben im Consumer.
Alternative Zielvariante: `hole_bestand` durch die Harvest-Adapter ersetzen
(Extra `sources`); dann liefert `result.snapshot_complete` die Vollständigkeit
für LA-06 und `result.issues` die bisher stillen Teilfehler.

## versteigerung (`janpow77/versteigerung`)

`backend/requirements.txt`: `auditcore_property_sources==0.1.0`.
In `backend/app/crawler/zvg_crawler.py`:

```python
from auditcore_property_sources import zvg as _ps

fix_mojibake = _ps.fix_mojibake
clean = _ps.clean
parse_de_number = _ps.parse_de_number
parse_money_amount = _ps.parse_money_amount
extract_market_value = _ps.extract_market_value
classify_type = _ps.classify_type
extract_address = _ps.extract_address
expand_street = _ps.expand_street
_norm_street = _ps.normalized_street
parse_listing_akten = _ps.parse_listing_akten


def decode_portal_response(response):
    return _ps.decode_portal_bytes(response.content)


def parse_detail(html, v):
    notice = _ps.parse_detail(
        html,
        _ps.ZvgNotice(
            zvg_id=v.zvg_id,
            land=v.land,
            court_id=v.court_id,
            file_number=v.file_number,
            court_name=v.court_name,
            detail_url=v.detail_url,
        ),
        reference_year=datetime.now().year,
    )
    for name, value in vars(notice).items():
        setattr(v, name, value)
    return v
```

`repair_market_values.py`, `reparse_addresses.py` und `regeocode.py`
importieren weiter aus `zvg_crawler` und erhalten dadurch die Bibliotheks-
funktionen. Geokodierung und `Ingest` (SQL) bleiben unverändert; der
Lebenszyklus kann optional mit `zvg_lifecycle` vor dem SQL-Schreiben geprüft
werden (identische Übergänge, siehe Replay-Test).

**Entschieden (PS-D01, 2026-09-23):** Detailabrufe (`showZvg`) laufen wie im
Original über den `ZvgDetailAdapter`, obwohl robots.txt sie sperrt
(`robots_policy="ignore"` ist Standard). Anhangsabrufe (`showAnhang`) bleiben
beim Consumer.
