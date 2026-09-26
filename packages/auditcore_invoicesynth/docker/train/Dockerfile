# Job-Image für das Donut-Nachtraining (Etappe E3), FlowAgent-Aktionsart train:donut.
# Gebaut von .github/workflows/donut-train-image.yml; Kontext = Repository-Wurzel.
# Basis nur mit Treiber-Umgebung (NVIDIA_*); CUDA 12.8 und cuDNN bringt das torch-cu128-Rad mit.
FROM nvidia/cuda:12.8.1-base-ubuntu24.04@sha256:133c78a0575303be34164d0b90137a042172bdf60696af01a3c424ab402d86e2

ARG WHEEL
ARG VCS_REF=unknown
# release: auditcore-Abhängigkeiten hashgebunden aus requirements-auditcore.txt;
# repo: aus demselben Repository-Stand gebaut (nur solange die Stände unveröffentlicht sind).
ARG AUDITCORE_DEPS=release
LABEL org.opencontainers.image.source="https://github.com/janpow77/auditcore" \
      auditcore.deps="${AUDITCORE_DEPS}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="auditcore-donut-train" \
      org.opencontainers.image.description="Donut-Nachtraining auditcore_invoicesynth (torch cu128)" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
       fonts-dejavu-core fonts-liberation fonts-liberation2 fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

COPY packages/auditcore_invoicesynth/docker/train/requirements-*.txt /tmp/req/
COPY dist/ /tmp/wheel/
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip==25.2 \
    && /opt/venv/bin/pip install --no-cache-dir \
       --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple \
       -r /tmp/req/requirements-train.txt \
    && if [ "$AUDITCORE_DEPS" = repo ]; then \
         /opt/venv/bin/pip install --no-cache-dir --no-deps /tmp/wheel/deps/*.whl; \
       else \
         /opt/venv/bin/pip install --no-cache-dir -r /tmp/req/requirements-auditcore.txt; \
       fi \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps "/tmp/wheel/${WHEEL}" \
    && /opt/venv/bin/pip check \
    && rm -rf /tmp/req /tmp/wheel

# Lizenzhinweise laut docs/provenance/donut.json (Modelle/Daten sind NICHT enthalten).
COPY packages/auditcore_invoicesynth/LICENSE /licenses/auditcore_invoicesynth-LICENSE
COPY packages/auditcore_invoicesynth/NOTICE /licenses/auditcore_invoicesynth-NOTICE
COPY docs/provenance/donut.json /licenses/donut-provenance.json
COPY packages/auditcore_invoicesynth/docker/train/THIRD_PARTY.md /licenses/THIRD_PARTY.md
RUN /opt/venv/bin/python -c "import json, importlib.metadata as m; print(json.dumps(sorted(({'name': d.metadata['Name'], 'version': d.version, 'license': d.metadata.get('License-Expression') or d.metadata.get('License') or '', 'classifiers': [c for c in d.metadata.get_all('Classifier') or [] if c.startswith('License')]} for d in m.distributions()), key=lambda x: x['name'].lower()), indent=1))" > /licenses/python-packages.json

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HOME=/tmp \
    HF_HOME=/tmp/hf \
    XDG_CACHE_HOME=/tmp/cache
WORKDIR /tmp
# Kein ENTRYPOINT: der FlowAgent-Job gibt das vollständige Kommando vor (job.json runs[].command).
CMD ["python", "-m", "auditcore_invoicesynth.train.cli", "--help"]
