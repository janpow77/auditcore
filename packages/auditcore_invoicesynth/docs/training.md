# Donut-Nachtraining (Etappe E3, vorbereitet)

Stand 24.09.2026. Plan: `docs/architecture/DONUT_OCR_PLAN.md` 2c/2c-bis,
Entscheidungen E1–E9 („Donut alle Empfehlungen“). **Es wurde kein echtes
Training ausgeführt**; janpow-ai ist offline. Vorhanden und getestet sind
Werkzeug, Profile, Checkpoint-/Wiederaufnahmelogik, Betriebsvorlagen und ein
CPU-Rauchtest mit winzigem Zufallsmodell.

## Bausteine (`auditcore_invoicesynth.train`)

| Baustein | Inhalt |
|---|---|
| `profiles` | `donut_train_janpow_ai` (Batch 4 je GPU, Akkumulation 2, AdamW, bf16, ≥ 14 GiB frei je Karte), `donut_train_8gb` (Batch 1, Akkumulation 16, 8-bit-AdamW, Gradient Checkpointing, ≥ 6,5 GiB frei), `cpu_smoke`; Startmodell `naver-clova-ix/donut-base@a959cf33…`; `config_hash` |
| `choose_topology` | aus GPU-Telemetrie: gleiche Kartenklasse ≥ 16 GiB → DDP (`torchrun --nproc_per_node=2`), ungleiche Karten → zwei Läufe (1280×960 / 1536×1152, Seed+1), eine Karte → single, keine → `unavailable` (kein stiller NUC-Rückfall) |
| `checkpoint` | atomar (`checkpoint-N.tmp` → fsync → `CHECKSUMS.sha256` → rename), alle 200 Schritte **oder** 15 Minuten, `save_total_limit=3`; beim Start neuester gültiger Checkpoint, Unvollständiges/Beschädigtes nach `rejected/` (mit Grund), Lauf-ID/Datensatz-/Konfigurations-Hash müssen passen |
| `loop` | deterministische Datenreihenfolge je Epoche (`Random(f"{seed}:{epoch}")`), Mikrobatches je Rang, JSON-Zeilen-Protokoll (Schritt, Epoche, Loss, VRAM-Spitze, Temperatur); Protokollzeilen nach dem letzten Checkpoint wandern beim Wiederaufnehmen nach `rejected/` |
| `torch_backend` (Extra `train`) | `VisionEncoderDecoderModel` nur aus lokalem Verzeichnis (`local_files_only`, optional SHA-256), Task-Token/Feld-Tags aus `schema.special_tokens()`, bf16-Autocast (CUDA), Gradient Checkpointing, AdamW/8-bit-AdamW, Cosinus-Scheduler mit Warm-up, DDP bei `WORLD_SIZE>1` (nur Rang 0 schreibt), Zustand: safetensors, Tokenizer, Prozessor, Optimierer, Scheduler, RNG |
| `ops` | VRAM-Startprüfung (`nvidia-smi`), systemd-Vorlage, FlowAgent-Jobbeschreibung |

## Aufrufe

```bash
# Rechenort planen (Telemetrie der Spokes als JSON) → FlowAgent-Job
auditcore-invoicesynth-train --profile donut_train_janpow_ai --dataset ds/ \
  --plan --gpus-json gpus.json > job.json
# Training; setzt automatisch am neuesten gültigen Checkpoint fort
torchrun --nproc_per_node=2 -m auditcore_invoicesynth.train.cli \
  --profile donut_train_janpow_ai --dataset ds/ --run-dir runs/r1 --base-model-dir base/donut-base
# NUC-Rückfall nur ausdrücklich
auditcore-invoicesynth-train --profile donut_train_8gb --dataset ds/ --run-dir runs/r1-nuc \
  --base-model-dir base/donut-base
# systemd --user-Dienst (xtts wird für den NUC-Rückfall pausiert, E7)
auditcore-invoicesynth-train --profile donut_train_8gb --systemd-unit --dataset ds/ \
  --run-dir runs/r1-nuc --base-model-dir base/donut-base \
  > ~/.config/systemd/user/auditcore-donut-train.service
```

Die Lauf-ID ist `sha256(Datensatz-Hash:Konfigurations-Hash)[:16]`; ein
Neustart desselben Auftrags findet dadurch seine Checkpoints wieder.

## Container-Vorlage (FlowAgent-Job-Image)

```dockerfile
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y --no-install-recommends python3-venv fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cu128 "torch>=2.7" \
    && /opt/venv/bin/pip install --no-cache-dir "auditcore_invoicesynth[train]==0.1.1" bitsandbytes
ENV PATH=/opt/venv/bin:$PATH HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ENTRYPOINT ["auditcore-invoicesynth-train"]
```

Image-Name in der Jobbeschreibung: `ghcr.io/janpow77/auditcore-donut-train:cu128`
(noch nicht gebaut/veröffentlicht).

## Nachweise dieser Runde (CPU, NUC, ohne GPU)

| Prüfung | Ergebnis |
|---|---|
| Stromausfall mit Ersatzmodell: Abbruch nach Schritt 6, halb geschriebener Checkpoint 8 | Wiederaufnahme ab 4, Loss-Verlauf und Endzustand identisch mit ununterbrochenem Lauf (`test_power_loss_resume_matches_uninterrupted_run`) |
| `kill -9` während eines laufenden Prozesses | Wiederaufnahme ab letztem gültigem Checkpoint, Schritte 1–40 lückenlos, Loss je Schritt identisch (`test_kill_9_during_training_resumes_from_last_valid_checkpoint`) |
| Winziges Donut-Modell (Swin 2 Stufen, MBart 1 Schicht, Zeichen-Tokenizer), 6 Schritte CPU, Abbruch nach 3, Wiederaufnahme | Loss von Schritt 3 vor/nach Wiederaufnahme gleich; Checkpoint enthält `model.safetensors`, Optimierer, Scheduler, RNG, Prüfsummen (`test_cpu_smoke_with_tiny_donut_model`; übersprungen ohne Extra `train`) |
| DDP mit `torchrun --nproc_per_node=2` (gloo, CPU) | 2 Ränge, ein Checkpoint von Rang 0 (manuell ausgeführt) |
| Rauchtest-Checkpoint in `auditcore_documents.LocalDonut` geladen | SHA-256 geprüft, Inferenz läuft (Zufallsausgabe), falsche Prüfsumme → `DONUT_MODEL_HASH_MISMATCH` (manuell ausgeführt) |

Getestet mit torch 2.14.0+cpu, transformers 5.17.0.

## Was für E3 auf janpow-ai noch fehlt

1. janpow-ai einschalten, als FlowAgent-Spoke registrieren (`install.sh --enroll`),
   Fähigkeit `train:donut` melden; Telemetrie beider GPUs prüfen (Name, VRAM) –
   die zweite Karte ist noch nicht erfasst; daraus entscheidet `choose_topology`
   zwischen DDP und zwei Läufen.
2. NVIDIA-Treiber ≥ 570 (Blackwell), CUDA 12.8; Train-Image bauen
   (Vorlage oben) oder venv mit `torch` cu128; ≥ 200 GB frei.
3. Startmodell `naver-clova-ix/donut-base@a959cf33c20e09215873e338299c900f57047c61`
   einmalig herunterladen, SHA-256 von `model.safetensors` festhalten und als
   `--base-model-sha256` übergeben (Training läuft danach offline).
4. Datensatz auf janpow-ai erzeugen oder übertragen und mit
   `auditcore-invoicesynth verify` gegen den Hash prüfen (Pilot: 2 000 Belege).
5. FlowAgent-Seite: Job-Typ `train:donut` annehmen, Fortschritt (Schritt,
   Loss, VRAM, Temperatur) aus `train-log.jsonl` melden, Checkpoint-Spiegelung
   zur NUC (rsync über Tailscale) nach jedem Checkpoint.
6. Echte Abnahme E3: Pilot 3 Epochen × 2 000, Stromausfall-Test auf der GPU
   (`kill -9` und hartes Ausschalten während eines Checkpoints), VRAM-Spitze
   messen, Pilot gegen Donut-CORD auf T1.
