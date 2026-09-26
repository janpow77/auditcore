# Drittkomponenten im Image auditcore-donut-train

Vollständige Liste mit Versionen und Lizenzangaben: `/licenses/python-packages.json`
(beim Bau aus den Paketmetadaten erzeugt). Herkunft und Entscheidungen:
`/licenses/donut-provenance.json` (Kopie von `docs/provenance/donut.json`).

| Komponente | Lizenz | Hinweis |
|---|---|---|
| auditcore_invoicesynth, auditcore_invoicegenerator, auditcore_dummygenerator | MIT | eigene Bibliotheken |
| torch (cu128, enthält CUDA-/cuDNN-/NCCL-Laufzeit von NVIDIA als pip-Pakete) | BSD-3-Clause; NVIDIA-Komponenten unter NVIDIA-Lizenzen (Weitergabe als Laufzeit erlaubt) | nur Laufzeit |
| transformers, tokenizers, safetensors | Apache-2.0 | – |
| sentencepiece | Apache-2.0 | – |
| Pillow | MIT-CMU | – |
| numpy | BSD-3-Clause | – |
| bitsandbytes | MIT | nur 8-bit-AdamW (Profil donut_train_8gb) |
| Basis nvidia/cuda:12.8.1-base-ubuntu24.04 | NVIDIA Deep Learning Container License, Ubuntu-Pakete | nur Treiber-Umgebung |
| fonts-dejavu-core / fonts-liberation(2) / fonts-noto-core | Bitstream Vera / OFL-1.1 / OFL-1.1 | Systemschriften für Datensatzbau |

**Nicht enthalten:** Modellgewichte (`naver-clova-ix/donut-base`, MIT, Revision
a959cf33…; Vergleichsmodell `donut-base-finetuned-cord-v2`, MIT), Datensätze,
Checkpoints. Sie werden zur Laufzeit schreibgeschützt eingehängt. Aus
clovaai/donut (MIT, © 2022-present NAVER Corp.) ist kein Code übernommen;
Modell und Prozessor kommen aus transformers.
