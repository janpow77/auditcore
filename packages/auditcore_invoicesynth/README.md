# auditcore_invoicesynth

## Zweck

Synthetische Trainings- und Testdaten für eine Donut-basierte Erkennung deutscher und österreichischer Rechnungen: Rechnungsbilder, Ziel-JSON, Manifest mit Datensatz-Hash und Bewertung.

Für das Belegerkennungs-Vorhaben nach `docs/architecture/DONUT_OCR_PLAN.md`
(Abschnitte 2b und 2d, Entscheidungen E1–E9 vom 24.09.2026). Grundlage sind
die Datensätze aus `auditcore_invoicegenerator`, der unverändert bleibt. Es
entstehen ausschließlich synthetische Belege; echte Belege und Fremddatensätze
(z. B. CORD) gehören nicht dazu (E3, E4).

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_invoicesynth[render]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.1 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-invoicesynth/`):

```text
auditcore_invoicesynth @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_invoicesynth-0.1.1-py3-none-any.whl#sha256=3d91e3d97e8bca8de7f909b731cbac72d989be835267805cabef81732a70709b
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-invoicesynth
```

Extras: `[render]` – Pillow ≥ 9.4 für Bilder und Scanrauschen (Debian:
`python3-pil`); `[train]` – torch ≥ 2.7, transformers, tokenizers,
sentencepiece, safetensors und Pillow für das Nachtraining (CPU- oder
cu128-Build über den Paketindex wählen); `[dev]` – Test- und Prüfwerkzeuge.

Befehlszeile (mit `[render]`):

```bash
auditcore-invoicesynth fonts                       # freie Systemschriften + SHA-256
auditcore-invoicesynth plan  --seed 42             # Plan ohne Bilder
auditcore-invoicesynth build --seed 42 --out ds/   # Pilot: 2 000 Belege
auditcore-invoicesynth verify ds/                  # Dateien + Datensatz-Hash prüfen
auditcore-invoicesynth evaluate ds/ --split test_layout_holdout --predictions p.jsonl
```

## Schnellstart

Der Kern läuft ohne Zusatzpakete: Plan, Anreicherung, Kennungen und Ziel-JSON.

```python
from decimal import Decimal
from random import Random

from auditcore_invoicesynth import (
    SynthConfig,
    fictional_bank_account,
    fictional_vat_id,
    from_sequence,
    iban_valid,
    plan_dataset,
    prepare_samples,
    to_sequence,
    vat_id_valid,
)

# Variantenplan und angereicherte Rechnungsdaten – ohne Bilder, ohne Pillow.
config = SynthConfig(
    seed=42,
    counts={"train": 3, "validation": 0, "test_synthetic": 0, "test_layout_holdout": 1},
)
specs = plan_dataset(config, ("DejaVu Sans",))
assert [spec.split for spec in specs] == ["train"] * 3 + ["test_layout_holdout"]
assert specs[-1].layout.startswith("holdout_")  # Holdout-Vorlagen nur im Testsatz

invoice = prepare_samples(config, specs)[0].invoice
assert invoice.net_amount + invoice.vat_amount == invoice.total  # exakt mit Decimal
assert isinstance(invoice.total, Decimal)

# Fiktive, aber prüfziffer-gültige Kennungen.
rng = Random(1)
assert vat_id_valid(fictional_vat_id(rng, "DE"))
account = fictional_bank_account(rng, "DE")
assert iban_valid(account.iban) and account.bic.startswith("SYNT")

# Ziel-JSON als Donut-Tokenfolge und zurück.
sequence = to_sequence({"invoice_number": "RE-2026-001", "total": "119,00 €"})
assert from_sequence(sequence) == {"invoice_number": "RE-2026-001", "total": "119,00 €"}
```

```pycon
>>> sequence
'<s_auditcore_invoice_v1><s_invoice_number>RE-2026-001</s_invoice_number><s_total>119,00 €</s_total>'
```

## API-Überblick

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

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_invoicesynth.__all__` (38):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ACCEPTANCE_THRESHOLDS` | Konstante | Abnahmeschwellen (Entscheidung E6 vom 24.09.2026) für T2 und T3. | `evaluation` |
| `ALLOWED_VAT_RATES` | Konstante | Zulässige Steuersätze je Land (Plausibilitätsprüfung, Bewertung). | `enrich` |
| `FONT_CATALOG` | Konstante | – | `fonts` |
| `HOLDOUT_LAYOUTS` | Konstante | – | `layout_model` |
| `LAYOUTS` | Konstante | – | `layout_model` |
| `SCHEMA_VERSION` | Konstante | – | `schema` |
| `SPLITS` | Konstante | – | `plan` |
| `TASK_TOKEN` | Konstante | – | `schema` |
| `TRAINING_LAYOUTS` | Konstante | – | `layout_model` |
| `DatasetError` | Ausnahme | Ausgabeverzeichnis belegt oder Datensatz beschädigt. | `dataset` |
| `EvaluationReport` | Datenklasse | – | `evaluation` |
| `FontError` | Ausnahme | Schrift fehlt, ist nicht frei lizenziert oder weicht von der Prüfsumme ab. | `fonts` |
| `FontSet` | Datenklasse | Gefundene Familien mit normaler und fetter Datei. | `fonts` |
| `SampleSpec` | Datenklasse | – | `plan` |
| `SynthConfig` | Datenklasse | – | `plan` |
| `SynthInvoice` | Datenklasse | Vollständiger synthetischer Beleg mit richtigen und gedruckten Werten. | `enrich` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `at_uid_check_digit` | Funktion | Prüfziffer der österreichischen UID (ATU + 8 Ziffern). | `identifiers` |
| `build_dataset` | Funktion | Datensatz schreiben und Manifest zurückgeben; das Zielverzeichnis muss leer sein. | `dataset` |
| `check_acceptance` | Funktion | Schwellen aus E6 prüfen (Feldgenauigkeit, Falschwert-Quote nach Plausibilität). | `evaluation` |
| `dataset_hash` | Funktion | – | `dataset` |
| `de_vat_check_digit` | Funktion | Prüfziffer der deutschen USt-IdNr. (ISO 7064, MOD 11,10). | `identifiers` |
| `discover_fonts` | Funktion | Katalogschriften in den Verzeichnissen suchen (erste Fundstelle in Pfadordnung). | `fonts` |
| `enrich` | Funktion | Generator-Datensatz → ``SynthInvoice``. | `enrich` |
| `evaluate` | Funktion | Paare (Ziel-JSON, Vorhersage) bewerten. | `evaluation` |
| `fetch_font` | Funktion | Schrift über den injizierten Abruf laden; nur bei passender SHA-256 speichern. | `fonts` |
| `fictional_bank_account` | Funktion | IBAN aus fiktiver BLZ-Liste und zufälliger Kontonummer. | `identifiers` |
| `fictional_vat_id` | Funktion | USt-IdNr. (DE) bzw. UID (AT) mit gültiger Prüfziffer. | `identifiers` |
| `from_sequence` | Funktion | Donut-Ausgabe → Ziel-JSON; unvollständige Tags werden übergangen. | `schema` |
| `iban_valid` | Funktion | Länge (DE/AT bekannt, sonst 15–34) und Modulo-97-Prüfung. | `identifiers` |
| `load_split` | Funktion | ``metadata.jsonl`` eines Satzes lesen: ``file_name``, ``gt_parse``, ``meta``. | `dataset` |
| `plan_dataset` | Funktion | Vollständiger Plan; ``font_families`` sind die tatsächlich verfügbaren Familien. | `plan` |
| `plan_summary` | Funktion | Plan und Ziel-JSON-Vorschau ohne Bilder (Kern ohne Extras). | `dataset` |
| `prepare_samples` | Funktion | Generator-Datensätze erzeugen und anreichern (ohne Pillow). | `dataset` |
| `special_tokens` | Funktion | Alle Zusatz-Token für den Tokenizer (Task, Feld-Tags, Trenner). | `schema` |
| `to_sequence` | Funktion | Ziel-JSON → Donut-Zielsequenz (ohne EOS; das setzt der Tokenizer). | `schema` |
| `vat_id_valid` | Funktion | Format und Prüfziffer für DE und AT; andere Länder sind hier nicht prüfbar. | `identifiers` |
| `verify_dataset` | Funktion | Dateien und Hash gegen das Manifest prüfen (ohne Pillow). | `dataset` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_invoicesynth.augment` | Prozedurales Scanrauschen mit Pillow (Extra ``render``), vollständig seed-bestimmt. |
| `auditcore_invoicesynth.cli` | Kommandozeile ``auditcore-invoicesynth``: fonts, plan, build, verify, evaluate. |
| `auditcore_invoicesynth.dataset` | Datensatz im Donut-Format: Bilder, ``metadata.jsonl`` je Satz, Manifest, Hash. |
| `auditcore_invoicesynth.enrich` | Anreicherung eines Generator-Datensatzes zu einem vollständigen deutschen Beleg. |
| `auditcore_invoicesynth.evaluation` | Bewertungswerkzeug (Plan 2d): gleiche Kennzahlen für alle Kandidaten. |
| `auditcore_invoicesynth.fonts` | Freie Schriften aus Systempaketen oder geprüftem Download – nie eingebettet. |
| `auditcore_invoicesynth.formats` | Deutsche und englische Zahlen-, Währungs- und Datumsformate samt Rücklesung. |
| `auditcore_invoicesynth.identifiers` | Prüfziffer-gültige, aber fiktive Kennungen (Entscheidung E5 vom 24.09.2026). |
| `auditcore_invoicesynth.labels` | Beschriftungs-Synonyme je Feld (deutsch überwiegend, englischer Anteil über den Plan). |
| `auditcore_invoicesynth.layout_body` | Positionstabelle, Summenblock, Zahlungshinweis, Bankverbindung und Fußzeile. |
| `auditcore_invoicesynth.layout_head` | Kopfbereich eines Belegs: Kennzeichnung, Absender, Empfänger, Titel, Kopfdaten. |
| `auditcore_invoicesynth.layout_model` | Belegvorlagen als Daten: Zeichenfläche, Vorlagenparameter und Formatwahl. |
| `auditcore_invoicesynth.layouts` | Zehn Belegvorlagen (acht fürs Training, zwei nur für den Layout-Holdout). |
| `auditcore_invoicesynth.plan` | Deterministischer Variantenplan und Aufteilung in Trainings-/Testsätze. |
| `auditcore_invoicesynth.render` | Pillow-Zeichenfläche für die Vorlagen (Extra ``render``). |
| `auditcore_invoicesynth.schema` | Ziel-JSON ``auditcore_invoice_v1`` (nur Kopf-/Summenfelder, Entscheidung E8). |
| `auditcore_invoicesynth.train` | Vorbereitetes Donut-Nachtraining (Plan 2c/2c-bis, Etappe E3). |
<!-- api-overview:end -->

## Profile und Konfiguration

- `SynthConfig`: `seed` (Standard 42), `base_date`, Aufteilung `counts`
  (Standard 1 600 / 150 / 150 / 100 für `train`, `validation`,
  `test_synthetic`, `test_layout_holdout`), `dpi_choices` (150/200/300),
  Anteile Englisch 10 %, Österreich 20 %, Fehlerfälle 10 %, Scanrauschen 85 %,
  Holdout-Vorlagen `holdout_kompakt`/`holdout_briefkopf` und Holdout-Schrift
  `DejaVu Serif`.
- Abnahmeschwellen der Bewertung: `ACCEPTANCE_THRESHOLDS` (E6).
- Nachtraining (Etappe E3, vorbereitet, kein echtes Training in 0.1.0):
  `auditcore_invoicesynth.train` bzw. `auditcore-invoicesynth-train` mit den
  Profilen `donut_train_janpow_ai` und `donut_train_8gb`, Rechenortwahl aus
  GPU-Telemetrie (DDP, zwei parallele Läufe oder „nicht verfügbar“ – kein
  stiller Rückfall auf den NUC), atomare Checkpoints mit Prüfsummen,
  deterministische Wiederaufnahme, systemd-Vorlage und FlowAgent-Job:
  [docs/training.md](docs/training.md).

**Reproduzierbarkeit:** Datensatz-Hash = SHA-256 über die sortierten Zeilen
`Pfad<TAB>SHA-256` aller Dateien außer dem Manifest. Gleicher Seed, gleiche
Konfiguration, gleiche Schriftdateien und gleiche Pillow-/zlib-Version ergeben
denselben Hash (Test `test_same_seed_same_hash_different_seed_different_hash`).
Das Manifest enthält keine Zeitstempel.

## Herkunft und Charakterisierung

Neuimplementierung in auditcore nach `docs/architecture/DONUT_OCR_PLAN.md`;
kein Code aus anderen Repositories und kein Donut-Code (clovaai/donut)
übernommen, daher keine Legacy-Charakterisierung. Baut auf
`auditcore_invoicegenerator` (`InvoiceScenario`: Parteien, Rechnungsnummer,
Positionen) auf. Entscheidungen E1–E8 (24.09.2026, „Donut alle Empfehlungen“)
stehen in `provenance.json`. Pilotnachweis: 2 000 Belege, bei gleichem Seed
derselbe Datensatz-Hash.

## Bewusste Verhaltensabweichungen

Keine – das Paket hat keinen Vorläufer. `auditcore_invoicegenerator` wird nur
genutzt, nicht verändert.

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_invoicegenerator==0.2.2` (bringt
`auditcore_dummygenerator` mit). Rendern (`[render]`) und Nachtraining
(`[train]`) nur mit den Extras. Schriften sind keine Paketabhängigkeit: es
werden freie Systemschriften (DejaVu, Liberation, Noto) gesucht oder mit
`fetch_font` und SHA-256 geladen.

## Sicherheit und Datenschutz

Rein synthetische Daten, keine echten Belege. Jede Seite trägt oben
„SYNTHETISCH – kein echter Beleg, Kennungen fiktiv“ und unten
„SYNTHETISCHE TRAININGSDATEN – nicht zahlen, keine Steuerwirkung“; der Builder
bricht ab, wenn eine Seite ohne beide Vermerke entstünde. Prüfziffer-gültige
IBAN und USt-IdNr. können zufällig realen Nummern entsprechen (E5); fiktive
BLZ beginnen mit 9 bzw. `99xxx`, BIC mit `SYNT`. Das Paket selbst öffnet
keine Netzwerkverbindung; `fetch_font` nutzt einen vom Aufrufer injizierten
Abruf und speichert nur Dateien aus dem Schriftkatalog mit passender SHA-256.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`), Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliothek; keine Umlizenzierung anderer Repositories. Schriften werden nicht
verteilt (Systempakete mit eigener freier Lizenz, Nachweis je Schrift im
Manifest). Details: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
