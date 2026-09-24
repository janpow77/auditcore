# Umsetzungsplan: Donut-basierte Belegerkennung mit auditcore

Stand: 24. September 2026. Status: **PLAN**, keine Implementierung, keine
fachliche Freigabe. Anlass: Nutzerfrage „kann man donut vision auch mit
auditcore selber erstellen?“ und Auftrag „plane donut“.

**Kurzantwort:** Ja. auditcore kann (1) die Trainingsdaten aus
`auditcore_invoicegenerator` erzeugen, (2) ein eigenes Donut-Modell für deutsche
Rechnungen nachtrainieren und (3) das Modell als OCR-Port in
`auditcore_documents` anbinden. Das heute eingesetzte CORD-Modell ist dafür
kein brauchbarer Ausgangspunkt (siehe [Abschnitt 3](#3-machbarkeitsprobe-ausgangswert));
nachtrainiert wird ab `donut-base`. Das Modell selbst gehört nicht ins
Repository und nicht in ein Wheel.

## Inhalt

1. [Lizenz- und Rechteklärung](#1-lizenz--und-rechteklärung)
2. [Architektur](#2-architektur)
3. [Machbarkeitsprobe (Ausgangswert)](#3-machbarkeitsprobe-ausgangswert)
4. [Etappen, Aufwand, Abschlusskriterien](#4-etappen-aufwand-abschlusskriterien)
5. [Risiken](#5-risiken)
6. [Offene Entscheidungen](#6-offene-entscheidungen)

## Ausgangslage (gelesen, nicht verändert)

| Baustein | Befund |
|---|---|
| `vision-service` (`~/Projekte/vision-service`, Image `ghcr.io/janpow77/vision-service:latest`) | FastAPI; `POST /v1/vision/parse` (multipart `image`, `model=donut-cord-v2`) liefert `raw`, `fields`, `json`, `duration_ms`, `device`; `POST /v1/ocr` (Tesseract, EasyOCR/Chandra optional); `GET /health`, `GET /v1/models`. Modell `naver-clova-ix/donut-base-finetuned-cord-v2`, im Build vorgeladen. |
| Betrieb auf der NUC | Container veröffentlicht **nur** `100.102.132.11:8015 → 8005` (Tailscale), nicht `localhost:8005`. `/health` meldet `device=cpu`, `gpu_available=false`: CPU-Torch 2.3.1 im Image, keine GPU-Freigabe im Container. |
| Feldabbildung im Service | `DonutBackend._extract_fields` sucht CORD-Tags per Regex (`<s_total…>`, `<s_date>`, `<s_num>` …). CORD kennt keine Rechnungsnummer, kein Datum, keine USt-IdNr., keine IBAN – die Treffer sind zufällig. |
| GPU | NVIDIA RTX 5060 Laptop, 8151 MiB; zur Zeit belegt ein fremder Prozess (xtts) rund 1,9 GiB. Blackwell (sm_120) benötigt Torch-Builds mit CUDA ≥ 12.8; die Pins des vision-service (`torch==2.3.1`, `transformers<4.50`) laufen dort nicht auf der GPU. |
| `auditcore_documents` 0.1.0 | Pipeline mit `OcrStage` und Ports `RouterOcr`, `ChandraPort`, `TesseractPort`, `Rasterizer`; `OcrBackend` = `auto/chandra/tesseract/none`. Felder entstehen in `PostprocessStage` per Regex: `invoice_number`, `date`, `total`, `net_amount`, `vat_amount`, `iban`, `vat_id`. Profile `LEGACY_PIPELINE` (bitgenau) und `CORRECTED_PIPELINE` = `RECOMMENDED_PIPELINE`. Extras: `ocr-raster`, `pdf-text`, `mime` u. a. |
| `auditcore_invoicegenerator` 0.2.0 | `InvoiceScenario` (DE/AT, Seed-deterministisch, Fehler `wrong_total`, `missing_vat_id`, `date_before_reference`), `render_pdf` (ReportLab-Extra). Das PDF hat **ein** Layout, englische Beschriftungen, ISO-Datumsangaben, Punkt als Dezimalzeichen, **keine IBAN** und als USt-IdNr. den sichtbaren Platzhalter `SYNTHETIC-NOT-A-REGISTERED-VAT-ID`. Für Trainingsdaten reicht das nicht. |
| Rauchtest | `auditcore.tools.deployer.smoke` kennt nur JSON-Anfragekörper (`json_body`), keinen Datei-Upload. |

## 1. Lizenz- und Rechteklärung

Geprüft am 24.09.2026 über die Hugging-Face-API und GitHub.

| Gegenstand | Quelle / Revision | Lizenz | Ins Repository? | Umgang |
|---|---|---|---|---|
| Donut-Code | `clovaai/donut` | MIT, © 2022-present NAVER Corp. | **Nein**, nicht nötig | Modell und Prozessor stellt `transformers` (Apache-2.0) bereit (`VisionEncoderDecoderModel`, `DonutProcessor`). Wird dennoch ein Stück übernommen (etwa `json2token` aus dem Trainingsbeispiel), dann mit Datei `LICENSES/donut-MIT.txt` und Eintrag in `NOTICE` des betreffenden Pakets. |
| Gewichte `naver-clova-ix/donut-base` | HF-Revision `a959cf33c20e09215873e338299c900f57047c61` | MIT (Modellkarte) | **Nein** | Download mit fester Revision und SHA-256 der Gewichtsdatei; Prüfsumme im Trainingsmanifest. Vortrainiert auf IIT-CDIP und SynthDoG; die Rechte an diesen Vortrainingsdaten klären wir nicht, wir übernehmen die MIT-Freigabe der Gewichte (Restrisiko: REVIEW_REQUIRED, niedrig). |
| Gewichte `…/donut-base-finetuned-cord-v2` | HF-Revision `8003d433113256b4ce3a0f5bf604b29ff78a7451` | MIT | **Nein** | Nur Vergleichsmodell (heutiger vision-service), **kein** Startpunkt fürs Nachtraining. |
| Datensatz CORD v2 | `naver-clova-ix/cord-v2`, Revision `7f0115a4b758a71d6473b8d085751692da2fef98`; GitHub `clovaai/cord` | CC-BY-4.0 | **Nein** | Indonesische Kassenbons, fachlich ungeeignet. Wird er (Entscheidung E3) als Beimischung gegen Vergessen genutzt, dann Namensnennung in der Modellkarte; das Modell bleibt dann weiter verteilbar (CC-BY verlangt nur Attribution). Empfehlung: nicht verwenden. |
| Eigene synthetische Daten | erzeugt aus `auditcore_invoicegenerator`/`auditcore_dummygenerator` (MIT, eigene Kerne) | eigene Daten | **Nur Generator, Manifest und höchstens eine Handvoll Beispielbelege als Testfixtures** | Datensatz ist aus Seed + Versionen reproduzierbar; im Repository steht das Manifest mit Datensatz-Hash, nicht die Bilder. Ablage des vollständigen Satzes lokal oder als Release-Asset. |
| Schriften für die Layouts | Systempakete `fonts-dejavu` (Bitstream-Vera-Lizenz), `fonts-liberation2` (OFL-1.1), `fonts-noto-core` (OFL-1.1) | frei | **Nein** | Nicht einbetten; Generator verlangt die Pfade als Konfiguration und schreibt Name, Paketversion und SHA-256 jeder Schriftdatei ins Manifest. |
| Scanrauschen, Hintergründe | prozedural (Pillow/NumPy) | eigen | ja (Code) | Keine Foto-/Textur-Datensätze fremder Herkunft. |
| Echte Belege | Prüf- oder Privatbelege | personenbezogen, ggf. Geschäftsgeheimnis | **Niemals** | Nur lokal, nur zur Evaluation, nur nach Entscheidung E4 (Rechtsgrundlage, Anonymisierung, Löschfrist). Nicht fürs Training, solange das Modell verteilt werden soll (Memorisierungsrisiko). |
| Nachtrainiertes Modell | eigene Gewichte, abgeleitet von MIT-Gewichten | Entscheidung E2 | **Nein** (kein Wheel, kein Git) | Release-Asset mit SHA-256 oder privates HF-Repository; Modellkarte mit MIT-Hinweis auf NAVER. |
| Laufzeitbibliotheken | `torch` (BSD-3), `transformers` (Apache-2.0), `sentencepiece` (Apache-2.0), `Pillow` (MIT-CMU) | frei | als Extra | Nur optionale Extras, nicht in der Kernabhängigkeit. |

Synthetische Kennungen: IBAN mit gültiger Prüfziffer (sonst lernt das Modell
keine realistische Struktur), aber aus einer fiktiven Bankleitzahlliste;
USt-IdNr. im Format `DE` + 9 Ziffern mit korrekter Prüfziffer. Beides kann
zufällig mit realen Nummern übereinstimmen; jede Seite bleibt sichtbar als
synthetisch markiert (wie im vorhandenen Renderer). Entscheidung E5.

## 2. Architektur

```
auditcore_invoicegenerator ──► auditcore_invoicesynth ──► Datensatz (Bild + Ziel-JSON + Manifest)
   (Rechnungsdaten)           (Layouts, Augmentierung,           │
                               Labels, Evaluation)               ▼
                                                     Nachtraining (NUC, RTX 5060, Checkpoints)
                                                                 │
                                                  Modellartefakt + Modellkarte + SHA-256
                                                    (Release-Asset / HF privat)
                                                                 │
                              ┌──────────────────────────────────┴──────────────┐
                              ▼                                                 ▼
        auditcore_documents[donut] (lokal, torch)          vision-service (/v1/vision/parse, GPU)
        auditcore_documents HttpDonut-Port  ──────────────►        ▲
                              ▲                                    │ llm-router / flow-agent
                              └──────────── flowinvoice-Pipeline ──┘
```

### 2a. OCR-Port-Adapter `donut` in `auditcore_documents`

Ziel: ein zusätzlicher Extraktionsweg, der strukturierte Felder liefert und
sich in die bestehenden Artefakte einfügt. `LEGACY_PIPELINE` bleibt bitgenau;
Donut ist nur über ein neues, ausdrücklich gewähltes Profil erreichbar.

**Port und Implementierungen**

```python
class DonutPort(Protocol):
    def available(self) -> bool: ...
    def parse(self, page_png: bytes) -> DonutResult: ...

@dataclass(frozen=True)
class DonutResult:
    fields: dict[str, Any]          # Ziel-JSON gemäß Schema (siehe unten)
    raw_sequence: str               # ungeparste Tokenfolge
    field_confidence: dict[str, float]  # min. Token-Wahrscheinlichkeit je Feld
    model_id: str                   # z. B. auditcore-donut-invoice-de@1.0.0
    model_sha256: str
    duration_ms: int
    device: str
```

| Implementierung | Abhängigkeiten | Zweck |
|---|---|---|
| `LocalDonut(model_dir, expected_sha256, device="auto")` | Extra `donut`: `torch`, `transformers`, `sentencepiece`, `pillow` | Offline-Inferenz im Prozess; lädt nur ein lokales Verzeichnis, **nie** aus dem Netz; verweigert das Laden bei abweichender Prüfsumme (`DONUT_MODEL_HASH_MISMATCH`). |
| `HttpDonut(post, base_url, model)` | keine (Transport als Port wie `fetch_url`/`post`) | Gegen den vision-service (`/v1/vision/parse`); ohne Port `DONUT_NOT_CONFIGURED` statt Netzwerkzugriff (analog PL-C08). |
| `FakeDonut` (Tests) | keine | Contract-Tests ohne Torch. |

Das Extra wird ohne Torch-Pin auf einen Index formuliert
(`donut = ["transformers>=4.46,<5", "torch>=2.7", "sentencepiece>=0.2", "pillow>=10"]`);
CPU- oder CUDA-Build wählt die Anwendung über ihren Paketindex. `mypy`-Override
für `torch.*`/`transformers.*`. Die Grenze `transformers<4.50` des vision-service
wird im Adapter nicht übernommen, sondern in E5 gegen die aktuelle Linie geprüft.

**Einbindung in die Stufen**

- `OcrBackend` erhält den Wert `donut` (additiv; `OcrSettings`-Validierung bleibt).
- `OcrStage._run_local("donut")`: PDF über den vorhandenen `Rasterizer` in
  Seitenbilder, je Seite `DonutPort.parse`. Die Seite mit den Summen (letzte
  Seite mit `total`) bestimmt die Kopffelder; Mehrseitigkeit wird in E5
  charakterisiert.
- Artefakte:
  - `artifacts.ocr_raw_json` = `{"engine": "donut", "model_id", "model_sha256", "pages": [{"fields", "raw_sequence", "field_confidence"}]}`
  - `artifacts.ocr_text` = zeilenweise Textdarstellung der erkannten Felder mit
    deutschen Beschriftungen (damit Watchdog und Regex-Rückfall arbeiten)
  - `artifacts.extracted_fields` wird von einer neuen Stufe
    `DonutFieldMergeStage` (nach `PostprocessStage`) gesetzt, siehe Tabelle.
  - `OcrMetrics`: `engine="donut"`, `avg_confidence`/`min_confidence` aus den
    Feldkonfidenzen der Pflichtfelder; `engine_version` = `model_id@sha256[:12]`.
- Profil: `DONUT_PIPELINE` (neue Profilversion, abgeleitet von
  `CORRECTED_PIPELINE`, Status zunächst `EXPERIMENTAL`). Voreinstellung in
  keinem bestehenden Profil.

**Abbildung Ziel-JSON → Pipeline-Felder**

| Ziel-JSON (`<s_auditcore_invoice_v1>`) | Pipeline-Feld | Normalisierung | Pflicht-Plausibilität |
|---|---|---|---|
| `invoice_number` | `invoice_number` | Leerraum trimmen | Länge 1–40, kein reines Datum/Betrag |
| `invoice_date` (wie gedruckt) | `date` | vorhandenes `normalize_date` → ISO | Datum gültig, nicht > 1 Jahr in der Zukunft |
| `net_amount` | `net_amount` | vorhandenes `parse_amount` (D5, gebietsschemabewusst) | ≥ 0 |
| `vat_lines[].amount` (Summe) | `vat_amount` | `parse_amount` | je Zeile `round(base × rate, 2)` ± 0,01 |
| `total` | `total` | `parse_amount` | `net + vat = total` ± 0,01 × Zeilenzahl |
| `iban` | `iban` | Großbuchstaben, ohne Leerzeichen | Länderlänge + ISO-13616-Prüfziffer (mod 97) |
| `supplier.vat_id` | `vat_id` | Großbuchstaben, ohne Leerzeichen | Format je Land, DE-Prüfziffer (ISO 7064 MOD 11,10) |
| `vat_lines[].rate` | (neu) `vat_rate` | Prozent als Dezimal | ∈ zulässige Sätze des Landes (DE 19/7/0, AT 20/13/10/0) |
| `supplier.name`, `supply_date`, `due_date`, `currency`, `bic` | zusätzliche Schlüssel | – | Fälligkeit ≥ Rechnungsdatum |

**Zusammenführung (verbindlich):** Ein Donut-Wert wird nur übernommen, wenn er
die Plausibilitätsprüfung besteht **und** entweder seine Feldkonfidenz über dem
Profilschwellwert liegt oder der gleiche Wert im Tesseract-Text vorkommt
(Zwei-Motoren-Abgleich für Beträge, IBAN, USt-IdNr.). Sonst bleibt der
Regex-Wert aus `PostprocessStage` bzw. das Feld leer und der Lauf wird
`REVIEW_NEEDED` (neue Regeln `VAL_DONUT_PLAUSIBILITY`, `VAL_DONUT_DISAGREEMENT`,
Stufe WARN). Ein Betrag aus Donut darf nie ungeprüft zu `OK` führen.

### 2b. Trainingsdaten-Werkzeug `auditcore_invoicesynth`

Eigenständige Distribution (Entscheidung E1), abhängig von
`auditcore_invoicegenerator==0.2.x`. Kern ohne schwere Abhängigkeiten
(Ziel-JSON, Varianten-Plan, Manifest, Bewertung); Extras `render`
(`reportlab`, `pypdfium2`, `pillow`) und `augment` (`numpy`, `pillow`).
Der charakterisierte PDF-Renderer 0.2.0 bleibt unverändert (Releases sind
unveränderlich); neue Layouts entstehen hier.

**Ablauf je Beleg:** `InvoiceScenario.generate(i)` → Anreicherung (IBAN, BIC,
USt-IdNr., Steuerzeilen, deutsches Format) → Layout-Renderer (PDF) →
Rasterung → Augmentierung → Paar (`image.png`, Ziel-JSON) + Manifestzeile.

**Variationsachsen**

| Achse | Werte (erste Ausbaustufe) |
|---|---|
| Layout | ≥ 8 Vorlagen: Kopf links/rechts, Tabelle mit/ohne Linien, Summenblock rechts/unten, Fußzeile mit Bankverbindung, zweispaltig, Kleinunternehmer-Hinweis, Gutschrift, mehrseitig; 2 Vorlagen nur im Testset (Layout-Holdout) |
| Beschriftungen | Synonymlisten („Rechnungsnummer“, „Rechnungs-Nr.“, „Beleg-Nr.“, „Invoice No.“; „Gesamtbetrag“, „Rechnungsbetrag“, „zu zahlen“, „Summe brutto“ …), DE überwiegend, EN-Anteil ≈ 10 % |
| Zahlenformate | `1.234,56`, `1234,56`, `1 234,56`, `1,234.56` (EN), Währung vor/nach dem Betrag, `EUR`/`€` |
| Datumsformate | `15.01.2026`, `15.1.26`, `15. Januar 2026`, `2026-01-15` |
| USt-Sätze | 19 %, 7 %, gemischt 19 + 7, 0 % mit Hinweis (§ 19 UStG, innergemeinschaftlich), AT 20/13/10 |
| Kennungen | IBAN DE/AT mit Prüfziffer, in Vierergruppen oder am Stück; USt-IdNr. DE/ATU; Steuernummer |
| Schriften | ≥ 6 Familien (DejaVu Sans/Serif, Liberation Sans/Serif/Mono, Noto Sans), Größen 8–12 pt, fett/normal |
| Scanrauschen | Drehung ±3°, leichte Perspektive, Unschärfe, JPEG-Artefakte, Salz-und-Pfeffer, Graustufe/Binarisierung, 150–300 dpi, Stempel/Kugelschreiber-Striche (prozedural), Lochung/Faltkante |
| Fehlerfälle | `wrong_total`, fehlende USt-IdNr., fehlende IBAN – das Ziel-JSON enthält dann das **Gedruckte**, nicht den korrigierten Wert (das Modell liest, die Validierung urteilt) |

**Ausgabeformat** (Donut-Konvention, direkt mit `datasets` ladbar):

```
dataset/
  manifest.json      # Generator-/Paketversionen, Seeds, Schriften (Name, Version, SHA-256),
                     # Varianten-Plan, Split-Regeln, SHA-256 je Datei, Datensatz-Hash
  train/metadata.jsonl   # {"file_name": "...png", "ground_truth": "{\"gt_parse\": {...}}"}
  validation/…  test_synthetic/…  test_layout_holdout/…
```

Datensatz-Hash = SHA-256 über die sortierte Liste `(Pfad, SHA-256)` aller Dateien.
Zwei Läufe mit gleichem Seed und gleichen Versionen müssen denselben Hash
liefern (Abschlusskriterium E2). Umfang: Pilot 2 000; Vollsatz 20 000 Training,
1 000 Validierung, 1 000 Test synthetisch, 500 Layout-Holdout.

### 2c. Nachtraining auf 8 GB VRAM

| Parameter | Wert (Start, in E3 gemessen und angepasst) | Begründung |
|---|---|---|
| Startmodell | `donut-base` (≈ 200 Mio. Parameter: Swin-B-Encoder + 4-lagiger BART-Decoder) | CORD-Aufgabe und -Tokens sind unpassend |
| Neue Tokens | Task-Token `<s_auditcore_invoice_v1>` + Feld-Tags `<s_invoice_number>` … | Decoder-Embeddings vergrößern (`resize_token_embeddings`) |
| Bildgröße | 1280 × 960 (Höhe × Breite), Hochformat | wie CORD; A4 bei 200 dpi wird herunterskaliert. Bei Lesefehlern kleiner Schrift Versuch mit 1536 × 1152 und Batch 1 |
| Decoder-Länge | 512 Token (Kopf-/Summenfelder); 768 erst mit Positionen | Speicher und Laufzeit |
| Präzision | bf16-Autocast (Blackwell unterstützt bf16); Gewichte in fp32 | stabiler als fp16 ohne Loss-Skalierung |
| Speicherhilfen | Gradient Checkpointing im Encoder; optional 8-bit-AdamW (`bitsandbytes`) | Optimiererzustand von ≈ 1,6 GB auf ≈ 0,4 GB |
| Batch | 1–2 pro Schritt, Gradient Accumulation 8–16 → effektiv 16 | passt nach Schätzung in ≈ 5–6 GB |
| Lernrate | 3e-5, Warm-up 300 Schritte, Cosinus-Abfall | Donut-Referenzwerte |
| Epochen | Pilot 3 × 2 000; Voll 5–8 × 20 000 mit Early Stopping auf Feld-Genauigkeit der Validierung | – |
| VRAM-Budget | 8 GiB minus Fremdbelegung; Trainingsstart verweigert, wenn < 6,5 GiB frei (xtts vorher beenden, Entscheidung E7) | kein OOM mitten im Lauf |
| Umgebung | eigenes venv/Container mit Torch ≥ 2.7 + CUDA 12.8 (sm_120); `transformers` aktuelle 4.x | vision-service-Pins laufen nicht auf Blackwell |

**Strom-/Wiederaufnahmefestigkeit (Pflicht):**

- Checkpoint alle 200 Optimiererschritte **und** alle 15 Minuten (was zuerst
  eintritt); `save_total_limit=3`, `safetensors`, Optimierer-, Scheduler-,
  RNG- und Dataloader-Zustand inklusive (HF `Trainer` bzw. eigener Loop mit
  identischem Inhalt).
- Atomar: in `checkpoint-N.tmp/` schreiben, `fsync`, Prüfsummendatei
  `CHECKSUMS.sha256` anlegen, dann umbenennen. Beim Start den **neuesten
  vollständigen** Checkpoint mit gültigen Prüfsummen wählen; unvollständige
  Verzeichnisse werden verworfen, nicht gelöscht (Nachweis).
- Start über `systemd --user`-Dienst `auditcore-donut-train.service` mit
  `Restart=on-failure` und automatischer Wiederaufnahme nach dem Hochfahren
  (abschaltbar); Lauf-ID, Datensatz-Hash und Konfiguration liegen im
  Checkpoint und müssen beim Wiederaufnehmen übereinstimmen.
- Deterministische Datenreihenfolge (Seed je Epoche), damit ein
  wiederaufgenommener Lauf dieselben Schritte sieht.
- Laufprotokoll (JSON-Zeilen: Schritt, Loss, VRAM-Spitze, Temperatur) für die
  Modellkarte; kein Cloud-Tracking.

Laufzeit-Schätzung (in E3 zu messen): 0,6–1,2 s je Beispiel → Vollsatz
(≈ 120 000 Beispielschritte) ≈ 20–40 GPU-Stunden, verteilt auf mehrere Nächte.

### 2c-bis. Rechenorte: janpow-ai (zwei GPUs) über den FlowAgent

Nutzerwunsch vom 24.09.2026: „Donut soll auch meine beiden gpus aus janpow ai
nutzen können.“ Es gilt der Grundsatz vom 28.08.2026 **„FlowAgent ist der
einzige GPU-Weg“** (so bereits für Whisper large-v3 auf der RTX 5070 Ti von
janpow-ai umgesetzt). Donut greift deshalb nie direkt per SSH/HTTP auf GPUs
zu, sondern über die Flow-Agent Control Plane (`agent.flowaudit.de`, Spokes
mit Fähigkeiten und Telemetrie).

| Rechenort | GPU(s) | Rolle für Donut | Zugang |
|---|---|---|---|
| **janpow-ai** (Tailscale 100.114.73.106) | 2 GPUs, u. a. RTX 5070 Ti 16 GB (zweite GPU beim ersten Kontakt per Telemetrie erfassen) | **Haupt-Trainingsort** und bevorzugter Inferenzort | FlowAgent-Spoke(s), Fähigkeiten `train:donut`, `ocr`/`vision` |
| NUC (100.102.132.11) | RTX 5060 Laptop 8 GB (+ optional eGPU) | Pilot-/Rückfall-Training (Profil 8 GB aus 2c), Inferenz-Rückfall | FlowAgent-Spoke `nuc-vision` (Tailscale-Adresse, nicht Docker-Name) |
| EVO-X2 | AMD, kein CUDA | nicht für Donut-Training (Torch/CUDA-Pfad) | – |

**Training auf zwei GPUs:**

- **Gleiche GPU-Klasse und ≥ 16 GB je Karte:** PyTorch DDP (`torchrun
  --nproc_per_node=2`), je GPU Batch 2–4 ohne 8-bit-Optimierer, effektive
  Batchgröße 16 über weniger Akkumulationsschritte; erwartete Laufzeit etwa
  halb so lang wie auf einer Karte. bf16 wie 2c.
- **Ungleiche Karten** (unterschiedlicher VRAM/Takt): kein DDP (die langsamere
  Karte bremst), stattdessen **zwei unabhängige Läufe parallel** – z. B.
  Bildgröße 1280×960 und 1536×1152 oder zwei Seeds – und Auswahl per
  Evaluation (2d). Entscheidung automatisch aus der Spoke-Telemetrie.
- Profil `donut_train_janpow_ai` mit eigenem VRAM-Budget je Karte; der
  8-GB-Pfad aus 2c bleibt als Profil `donut_train_8gb` für die NUC erhalten.
- Wiederaufnahme wie 2c (atomare Checkpoints mit Prüfsummen). Checkpoints
  liegen auf janpow-ai lokal und werden nach jedem Checkpoint zusätzlich auf
  die NUC gespiegelt (rsync über Tailscale), damit ein Lauf bei Ausfall von
  janpow-ai auf der NUC weiterlaufen kann (mit 8-GB-Profil, gleiche Lauf-ID).
- Auftrag über den FlowAgent als Job (Container-Image mit Torch ≥ 2.7/CUDA
  12.8, Datensatz per Hash, Konfiguration, Ziel-Checkpoint-Pfad); der FlowAgent
  meldet Fortschritt (Schritt, Loss, VRAM, Temperatur) zurück. Ist janpow-ai
  offline (Stand 24.09.2026: seit 24 Tagen offline), startet kein Lauf dort;
  die Planung zeigt den Rechenort „nicht verfügbar“ statt still auf die NUC
  auszuweichen – der Rückfall auf die NUC ist eine ausdrückliche Wahl.

**Inferenz:** Das nachtrainierte Modell wird als Fähigkeit `ocr`/`vision`
(Modellname `auditcore-donut-invoice-v1`) auf den GPU-Spokes von janpow-ai
bereitgestellt; der vision-service der NUC bleibt Rückfall. flowinvoice ruft
wie heute nur die Plattform auf (`/api/v1/ai/apps/flowinvoice/v1/ocr`); die
Plattform wählt den Spoke. Spokes melden ausschließlich über Tailscale
erreichbare Adressen (Lehre aus dem OCR-Ausfall vom 24.09.2026: Docker-
Containernamen sind von Hetzner aus nicht auflösbar).

**Voraussetzungen vor E3:** janpow-ai einschalten und als FlowAgent-Spoke
registrieren (Ein-Befehl-Installer `install.sh --enroll`), Telemetrie beider
GPUs prüfen, NVIDIA-Treiber ≥ 570 für Blackwell, freier Plattenplatz ≥ 200 GB
für Datensatz, Checkpoints und Container.

### 2d. Evaluation

Ein gemeinsames Bewertungswerkzeug (`auditcore_invoicesynth.eval`, rein
Python, Motoren über Ports) bewertet alle Kandidaten auf denselben Testsätzen.

| Metrik | Definition |
|---|---|
| Feldgenauigkeit | je Feld exakter Treffer nach Normalisierung: Betrag als `Decimal` auf den Cent, Datum ISO, Rechnungsnummer als String, USt-IdNr./IBAN ohne Leerzeichen, groß |
| Falschwert-Quote | Feld ausgegeben, aber falsch (schlimmer als „fehlt“) – getrennt von der Fehlt-Quote |
| Halluzinationsquote | ausgegebener Wert, der auf dem Beleg nicht vorkommt (Abgleich mit Ground-Truth-Text) |
| Belegquote | alle Pflichtfelder (Gesamtbetrag, Datum, Rechnungsnummer, USt-IdNr., IBAN) richtig |
| Nach Plausibilität | Falschwert-Quote der Werte, die die Zusammenführung aus 2a als `OK` durchlässt – **die maßgebliche Kennzahl** |
| Abdeckung/Konfidenz | Anteil automatisch übernommener Felder je Konfidenzschwelle |
| Laufzeit | Median/95-Perzentil je Seite, CPU und GPU |
| nTED | Baumabstand des gesamten JSON (Donut-Standard), nur ergänzend |

**Kandidaten:** (1) vision-service Donut-CORD, (2) Tesseract + Regex
(`CORRECTED_PIPELINE`), (3) Chandra + Regex (in flowinvoice lokal; im
vision-service derzeit `available=false`), (4) nachtrainiertes Donut,
(5) Donut + Tesseract-Abgleich (Zusammenführung aus 2a).

**Testsätze:**

| Satz | Inhalt | Zweck |
|---|---|---|
| T1 | 1 000 synthetische Belege, Layouts wie im Training | Lernerfolg |
| T2 | 500 synthetische Belege aus 2 zurückgehaltenen Layouts und einer zurückgehaltenen Schrift | Verallgemeinerung |
| T3 | 100–200 synthetische Belege **ausgedruckt und gescannt/fotografiert** | echtes Papier-/Kamerarauschen ohne Personenbezug |
| T4 | echte Belege, anonymisiert (optional, E4) | Realitätsnähe; nur lokal, nie im Repository, Ergebnisse nur aggregiert |

**Abnahmeschwellen (Vorschlag, E6):** auf T2 und T3 Gesamtbetrag ≥ 98 %,
Datum ≥ 98 %, Rechnungsnummer ≥ 95 %, IBAN und USt-IdNr. ≥ 97 %;
Falschwert-Quote nach Plausibilität ≤ 0,5 % je Feld; auf T3 besser als
Tesseract + Regex in mindestens vier der fünf Pflichtfelder.

### 2e. Versionierung, Provenienz, Auslieferung, Integration

- **Modellkennung:** `auditcore-donut-invoice-de`, SemVer (`1.0.0`); Major bei
  Schemaänderung des Ziel-JSON (Task-Token trägt die Schemaversion).
- **Modellkarte** (`MODEL_CARD.md` im Artefakt, Kopie unter
  `docs/provenance/` im Repository): Startmodell mit HF-Revision, SHA-256 und
  MIT-Hinweis NAVER; Datensatz-Hash und Manifest; Generator-, Paket- und
  Code-Commit; Hyperparameter; Laufprotokoll-Hash; Metriken je Testsatz und
  Kandidat; bekannte Grenzen (keine Handschrift, keine Kassenbons, nur DE/AT);
  Einsatzhinweis: Vorschlagswerte mit Pflicht-Plausibilitätsprüfung, keine
  automatische Entscheidung über Förderfähigkeit.
- **Artefakt:** `model.safetensors` (fp16, ≈ 400 MB) + Prozessor-/Tokenizer-
  Dateien + `MODEL_CARD.md` + `manifest.json`, als `tar.zst` mit SHA-256.
  Ablage als **GitHub-Release-Asset** (`donut-invoice-de-v1.0.0`) im
  auditcore-Repository oder privates HF-Repository (E2). Kein Git-LFS, kein Wheel.
- **Bezug:** Befehl `auditcore-documents donut fetch --version 1.0.0 --dest …`
  (Extra `donut`) lädt, prüft SHA-256 und entpackt; Laufzeit arbeitet danach
  offline. Für APT: eigenes Datenpaket `auditcore-donut-model-de` (arch-all)
  mit Prüfsumme, nicht Teil der Bibliothekspakete.
- **vision-service:** Modellverzeichnis per Volume, `VISION_DONUT_MODEL=/models/donut-invoice-de-1.0.0`;
  neuer Modellname `donut-invoice-de` in `/v1/models`; `_extract_fields`
  erhält eine zweite Abbildung für das Task-Token `<s_auditcore_invoice_v1>`
  (die CORD-Regex bleibt für `donut-cord-v2`); Hash-Prüfung beim Laden;
  GPU-Variante des Images (Torch cu128, `deploy.resources.reservations.devices`)
  oder bewusst CPU-Betrieb (E7). Änderungen dort in dessen Repository.
- **flowinvoice:** nach Release von `auditcore_documents` mit Donut-Port stellt
  flowinvoice über `HttpDonut` (Transport = vorhandener `ai_router_client`,
  `model="donut"`) auf `DONUT_PIPELINE` um – zunächst im Schattenbetrieb
  (Donut-Ergebnis wird protokolliert, Entscheidung weiter über Regex), dann
  schaltbar je Mandant.
- **Pflicht-Rauchtest** (`docs/deployment/functional-smoke.md`): Der Runner
  kann heute nur JSON-Körper senden. Zwei Wege, beide in E6:
  (a) Rauchtest-Fall über die flowinvoice-API (synthetischen Beleg
  `AUDITCORE-SMOKE` hochladen, Ergebnis `extracted_fields.total` mit Erwartung
  `{"min": x, "max": x}` prüfen, danach löschen) – bevorzugt, weil er die
  ganze Kette prüft; (b) Erweiterung des Runners um `file_body`
  (multipart) für den direkten vision-service-Fall.

## 3. Machbarkeitsprobe (Ausgangswert)

**Durchführung (24.09.2026):** `InvoiceScenario(42, base_date=2026-01-15, country="DE").generate_batch(5)`
aus `auditcore_invoicegenerator` 0.2.0; jeder Beleg in zwei Varianten:
(A) vorhandenes `render_pdf`, mit pypdfium2 bei 200 dpi gerastert;
(B) dieselben Daten in einem einfachen deutschen Layout (deutsche
Beschriftungen, `1.234,56`, `TT.MM.JJJJ`, Beispiel-USt-IdNr. und -IBAN),
nur für die Probe mit Pillow gezeichnet. Je Bild ein Aufruf
`POST /v1/vision/parse` (`model=donut-cord-v2`) und zum Vergleich
`POST /v1/ocr` (`backend=tesseract`, `lang=deu+eng`) gegen den laufenden
vision-service (`http://100.102.132.11:8015`), nacheinander, keine
Konfigurationsänderung. Bewertung: Donut-Treffer nur, wenn der Wert im
passenden CORD-Feld bzw. in `fields` steht (Betrag auf den Cent); für
Rechnungsnummer und Datum (CORD hat keine solchen Felder) genügt das Vorkommen
in der Rohsequenz. Tesseract: Wert kommt im Text vor. Skript und Rohausgaben
liegen nicht im Repository (Scratch), die Probe ist mit obigem Seed
wiederholbar.

**Ergebnis (5 Belege × 2 Varianten, Treffer je Feld):**

| Feld | Donut-CORD, Variante A (Generator-PDF) | Donut-CORD, Variante B (deutsches Layout) | Tesseract-Text, A | Tesseract-Text, B |
|---|---|---|---|---|
| Gesamtbetrag | 0/5 | 1/5 | 5/5 | 5/5 |
| Nettobetrag | 0/5 | 1/5 | 5/5 | 5/5 |
| Steuerbetrag | 0/5 | 0/5 | 5/5 | 5/5 |
| Rechnungsnummer (nur in Rohsequenz) | 5/5 | 5/5 | 5/5 | 5/5 |
| Rechnungsdatum (nur in Rohsequenz) | 0/5 | 5/5 | 5/5 | 5/5 |
| IBAN (nur B) | – | 1/5 | – | – |
| USt-IdNr. (nur B) | – | 4/5 | – | – |
| Laufzeit je Seite (Median, CPU) | 131 s | 93 s | 2,0 s | 1,5 s |

**Feldausgabe des vision-service (`fields`), über alle 10 Bilder:**
`total_amount` 1/10 richtig, `invoice_number` 0/10 (ausgegeben wurden
„TechCorp GmbH“, „Document: DOC-0001“, „97,50667 K6In“), `invoice_date` nie
gesetzt.

**Beobachtungen:**

- Das CORD-Modell liest den Text teilweise (Rohsequenz enthält Rechnungsnummer
  und in Variante B das Datum), ordnet ihn aber Speisekarten-Feldern zu
  (`<s_nm>`, `<s_num>`, `<s_price>`); Rechnungsfelder kennt es nicht.
- **Betragsfehler, die ohne Prüfung gefährlich wären:** vertauschte Felder
  (DOC-00003: `total` = Steuerbetrag 510,65, `subtotal` = Gesamtbetrag,
  `tax` = Nettobetrag), eingefügte Ziffern (`18.251,004` statt 18.251,04;
  `160703.90` statt 16703.90), falsche Trennzeichen (`3.467.70`,
  `7,610,06`), gelesene Datumsziffern falsch (`202-01-15`).
- Tesseract findet alle Werte als Text (der Vergleich prüft nur das Vorkommen,
  nicht eine Feldzuordnung); die Feldzuordnung leistet dort die Regex-
  Nachverarbeitung aus `auditcore_documents`.
- Laufzeit auf der CPU (85–150 s je Seite) ist für den Stapelbetrieb zu langsam.

**Ausgangswert:** Donut-CORD liefert auf deutschen Rechnungen **keine
verwertbaren Feldwerte** (Feldtreffer ≈ 0–20 %, mit Vertauschungen). Das
bestätigt: Nachtraining ab `donut-base` mit eigenem Ziel-Schema ist nötig,
und jede Donut-Ausgabe braucht die Plausibilitätsprüfung aus 2a. Maßstab für
das eigene Modell ist Tesseract + Regex, nicht das CORD-Modell.

## 4. Etappen, Aufwand, Abschlusskriterien

Aufwand in Arbeitstagen (AT) für die Umsetzung plus GPU-Zeit (unbeaufsichtigt).

| Etappe | Inhalt | Aufwand | Abschlusskriterium |
|---|---|---|---|
| E0 | Entscheidungen E1–E8 einholen; Lizenzvermerke (Abschnitt 1) in `docs/provenance/` | 0,5 AT | Entscheidungen dokumentiert (DECIDED mit Datum/Zitat) |
| E1 | Bewertungswerkzeug + T1/T2-Miniaturen (je 50) + Ausgangswerte aller verfügbaren Kandidaten | 1–2 AT | reproduzierbarer Ausgangswert-Bericht in `docs/reports/`; Bewertungslogik mit Unit-Tests |
| E2 | `auditcore_invoicesynth`: Anreicherung, ≥ 8 Layouts, Schriften, Augmentierung, Manifest, Splits; Paketgerüst mit Tests, Provenienz, Quality Gates | 4–6 AT | Pilot 2 000 Belege; zweiter Lauf gleicher Hash; Sichtprüfung von 50 zufälligen Belegen ohne Befund; `pytest`, `ruff`, `mypy --strict`, `auditcore-bibquality` grün |
| E3 | Trainingswerkzeug mit Checkpoint-/Wiederaufnahme-Logik; Pilotlauf 3 Epochen × 2 000 | 2–3 AT + ≈ 4 GPU-h | **Stromausfall-Test:** `kill -9` und hartes Ausschalten während Schreiben eines Checkpoints → Wiederaufnahme ab letztem vollständigem Checkpoint, Schrittzähler und Loss-Verlauf stimmen; VRAM-Spitze gemessen ≤ 7 GiB; Pilot schlägt Donut-CORD auf T1 deutlich |
| E4 | Vollsatz erzeugen, Volltraining, Evaluation T1–T3 (T3 drucken/scannen) | 2–3 AT + 20–40 GPU-h | Abnahmeschwellen aus 2d erreicht oder begründeter Abbruch mit Befund; Modellkarte vollständig |
| E5 | `auditcore_documents`: `DonutPort`, `LocalDonut`/`HttpDonut`/`FakeDonut`, `DonutFieldMergeStage`, Profil `DONUT_PIPELINE`, Extra `donut`, CLI `donut fetch`; neue Minor-Version | 3–4 AT | `LEGACY_PIPELINE`-Fingerabdruck unverändert (alle 30 Läufe); Contract-Tests mit `FakeDonut`; installiertes Wheel mit Extra führt einen echten Beleg durch; CI grün |
| E6 | Release-Asset + Hash; vision-service mit neuem Modell (GPU- oder CPU-Variante); flowinvoice Schattenbetrieb; Rauchtest-Fall (2e) | 2–3 AT | `auditcore-deploy smoke` **PASS** gegen die laufende Anwendung mit geprüftem Betrag; Schattenbetrieb liefert Vergleichsprotokoll über ≥ 1 Woche |

Summe: **≈ 15–21 AT** zuzüglich **≈ 1–2 Tage GPU-Laufzeit**. E1 und der Beginn
von E2 sind unabhängig von der GPU; E5 kann mit `FakeDonut` parallel zu E3/E4
laufen.

## 5. Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| **Halluzinierte Beträge** (in der Probe beobachtet: Beträge in falschen Feldern, zusätzliche Ziffern, Zahlen doppelt) | falscher Betrag wird als Prüfgrundlage übernommen | Plausibilitätsprüfung und Zwei-Motoren-Abgleich sind **Pflicht** (2a); Falschwert-Quote nach Plausibilität als Abnahmekennzahl; Donut allein führt nie zu `OK` |
| VRAM 8 GiB, Fremdbelegung (xtts ≈ 1,9 GiB) | OOM, Abbruch | Speicherhilfen (2c); Startprüfung auf freien Speicher; Lauf nur, wenn andere GPU-Dienste pausieren (E7) |
| Instabile Stromversorgung | Verlust von Trainingsfortschritt, beschädigte Checkpoints | atomare, geprüfte Checkpoints alle 15 min; Wiederaufnahme per systemd; Stromausfall-Test als Abschlusskriterium E3 |
| Laptop-GPU drosselt thermisch | Laufzeit verdoppelt sich | Temperatur im Laufprotokoll; Nachtläufe; Leistungsgrenze nur, wenn der Treiber sie erlaubt |
| Blackwell/Torch-Kompatibilität | Training nur auf CPU möglich | eigene Umgebung mit Torch ≥ 2.7/cu128; in E3 zuerst prüfen |
| Daten-Drift synthetisch → echt | gute Testwerte, schwache Praxis | Layout-Holdout (T2), Druck-Scan-Satz (T3), Schattenbetrieb in flowinvoice, optional T4 |
| Überanpassung an Generator-Eigenheiten (Positionskataloge, Firmennamen) | Modell lernt Kataloge statt Lesen | Kataloge für Testsätze trennen; zufällige Zeichenketten in einem Teil der Felder |
| Mehrseitige Belege | Summen auf Seite 2 werden übersehen | Seitenweise Inferenz, Summenseite bestimmen; mehrseitige Vorlagen im Training |
| Kleine Schrift bei 1280 × 960 | Ziffern verwechselt (in der Probe: `18.251,004`) | Versuch mit größerer Eingabe; Zuschnitt auf den Summenblock als zweiter Durchlauf |
| CPU-Betrieb des vision-service | 85–130 s je Seite in der Probe | GPU-Image oder Inferenz nur asynchron im Worker (E7) |
| Rechte an Vortrainingsdaten von `donut-base` | Rest-Unsicherheit | MIT-Freigabe der Gewichte dokumentieren; REVIEW_REQUIRED (niedrig) |
| Synthetische Kennungen kollidieren mit realen | Anschein realer Daten | sichtbare Synthetik-Kennzeichnung; fiktive BLZ-Liste (E5) |

## 6. Offene Entscheidungen

| Nr. | Frage | Empfehlung |
|---|---|---|
| E1 | Trainingsdaten als neue Distribution `auditcore_invoicesynth` oder als Extra von `auditcore_invoicegenerator` 0.3.0? | neue Distribution (klar getrennter Zweck, Generator bleibt schlank und charakterisiert) |
| E2 | Lizenz und Ablage des nachtrainierten Modells: öffentlich (MIT, Release-Asset) oder privat (HF privat)? | MIT + öffentliches Release-Asset, solange nur synthetische Daten eingehen |
| E3 | CORD v2 beimischen? | nein |
| E4 | Echte anonymisierte Belege für die Evaluation (T4)? Wenn ja: Rechtsgrundlage, Anonymisierungsverfahren, Löschfrist | zunächst nein; eigene Privatbelege oder gedruckte Synthetik (T3) genügen für die Abnahme |
| E5 | Prüfziffer-gültige, aber fiktive IBAN/USt-IdNr. in den Trainingsbelegen? | ja, mit sichtbarer Synthetik-Kennzeichnung |
| E6 | Abnahmeschwellen aus 2d bestätigen | wie vorgeschlagen |
| E7 | Betrieb: Training und Inferenz auf den zwei GPUs von janpow-ai über den FlowAgent (Nutzerwunsch 24.09.2026); NUC nur als Rückfall. Darf xtts auf der NUC für Rückfall-Trainingsnächte pausieren? | janpow-ai als Hauptort (DDP bei gleichen Karten, sonst zwei parallele Läufe); NUC-Rückfall nur ausdrücklich; xtts-Pause ja |
| E9 | janpow-ai dauerhaft betreiben (Strom/Kosten) oder nur für Trainingsläufe einschalten? | nur für Trainingsläufe und bei Bedarf für Inferenz; Rückfall NUC |
| E8 | Umfang Version 1: nur Kopf-/Summenfelder oder auch Positionen? | nur Kopf-/Summenfelder; Positionen in Version 2 |
