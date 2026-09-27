# auditcore-runner: ephemerer GitHub-Actions-Runner mit gepinnten Prüfwerkzeugen.
# Basis: offizielles Runner-Image (MIT). `auditcore-runner image aktualisieren`
# setzt BASE auf den Digest des neuesten Runner-Release (Pflicht: ≥ v2.329.0,
# neue Releases binnen 30 Tagen). Werkzeuge und Lizenzen: THIRD_PARTY.md.
ARG BASE=ghcr.io/actions/actions-runner@sha256:e5496277be5d09bc968b3d64911b74e219ac4a3f2edce956a3ecf9271bea1ef4
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424
FROM ${UV_IMAGE} AS uv
FROM ${BASE}

USER root

# Systembibliotheken, die Tests auf ubuntu-latest vorfinden: Compiler, PDF-/Bild-
# Renderer (Pango, Cairo), XML, Schriften und deutsche Locale.
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential pkg-config git curl ca-certificates jq unzip zstd xz-utils \
      libffi-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev liblzma-dev \
      libxml2 libxslt1.1 \
      libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
      libharfbuzz0b libjpeg-turbo8 libopenjp2-7 shared-mime-info \
      fonts-dejavu-core fonts-liberation fonts-noto-core fonts-noto-color-emoji locales \
 && sed -i 's/^# *de_DE.UTF-8/de_DE.UTF-8/' /etc/locale.gen \
 && locale-gen \
 && rm -rf /var/lib/apt/lists/*

# Werkzeug-Pins: werkzeuge/binaer.json (Binärdateien mit SHA-256), requirements*.txt
# (Python, Dependabot pip), package.json + package-lock.json (Node, Dependabot npm).
COPY werkzeuge/ /tmp/werkzeuge/

# Binärdateien und Node, jede Datei gegen ihre SHA-256 geprüft (trivy nur so, siehe binaer.json).
RUN bash /tmp/werkzeuge/installieren.sh /tmp/werkzeuge/binaer.json

# uv (MIT/Apache-2.0) und die Python-Werkzeuge, je in eigener Umgebung, versionsgenau.
COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_TOOL_DIR=/opt/tools UV_TOOL_BIN_DIR=/usr/local/bin UV_PYTHON_INSTALL_DIR=/opt/python
RUN grep -vE '^[[:space:]]*(#|$)' /tmp/werkzeuge/requirements.txt | xargs -n1 uv tool install \
 && uv venv /opt/libcst \
 && uv pip install --python /opt/libcst/bin/python -r /tmp/werkzeuge/requirements-libcst.txt \
 && printf '#!/bin/sh\nexec /opt/libcst/bin/python -m libcst.tool "$@"\n' > /usr/local/bin/libcst-tool \
 && chmod 0755 /usr/local/bin/libcst-tool

# Node-Werkzeuge aus dem Lockfile; Playwright-Chromium mit Systemabhängigkeiten und
# festen Schriften (stabile Screenshots). Lighthouse CI nutzt denselben Browser.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN mkdir -p /opt/node-tools \
 && cp /tmp/werkzeuge/package.json /tmp/werkzeuge/package-lock.json /opt/node-tools/ \
 && cd /opt/node-tools && npm ci --no-audit --no-fund \
 && ./node_modules/.bin/playwright install --with-deps chromium \
 && ln -sf "$(ls -d /opt/ms-playwright/chromium-*/chrome-linux*/chrome | head -n1)" /usr/local/bin/chromium \
 && chmod -R a+rX /opt/ms-playwright /opt/node-tools \
 && rm -rf /var/lib/apt/lists/* /root/.npm /tmp/werkzeuge
ENV PATH=/opt/node-tools/node_modules/.bin:$PATH \
    CHROME_PATH=/usr/local/bin/chromium \
    NODE_PATH=/opt/node-tools/node_modules

# Verzeichnisse für Werkzeug- und Paket-Cache vorab anlegen, damit Docker neue
# benannte Volumes mit den Rechten des Runner-Nutzers initialisiert. Der
# Runner-Nutzer verliert sudo und docker.
RUN mkdir -p /home/runner/_work/_tool /home/runner/.cache/uv /home/runner/.npm /cache \
 && chown -R runner:runner /home/runner/_work /home/runner/.cache /home/runner/.npm \
 && chmod 1777 /cache \
 && gpasswd -d runner sudo && gpasswd -d runner docker \
 && rm -f /etc/sudoers.d/runner

USER runner
ENV RUNNER_TOOL_CACHE=/home/runner/_work/_tool \
    AGENT_TOOLSDIRECTORY=/home/runner/_work/_tool

LABEL org.opencontainers.image.title="auditcore-runner" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/janpow77/auditcore"

# Die JIT-Konfiguration kommt als eingebundene Datei (nicht in `docker inspect`);
# die Umgebungsvariable bleibt als Rückfall für ältere Supervisoren.
ENTRYPOINT ["/bin/bash", "-c", "if [ -r /run/auditcore/jit ]; then jit=\"$(cat /run/auditcore/jit)\"; else jit=\"$AUDITCORE_JIT_CONFIG\"; fi; unset AUDITCORE_JIT_CONFIG; exec /home/runner/run.sh --jitconfig \"$jit\""]
