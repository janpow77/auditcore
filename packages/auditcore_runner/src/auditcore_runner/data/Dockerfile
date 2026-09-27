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
      fonts-dejavu-core fonts-liberation locales \
 && sed -i 's/^# *de_DE.UTF-8/de_DE.UTF-8/' /etc/locale.gen \
 && locale-gen \
 && rm -rf /var/lib/apt/lists/*

# uv (MIT/Apache-2.0) und die Python-Werkzeuge (MIT), versionsgenau.
COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_TOOL_DIR=/opt/tools UV_TOOL_BIN_DIR=/usr/local/bin UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv tool install ruff==0.16.9 \
 && uv tool install mypy==2.3.1 \
 && uv tool install zizmor==1.30.1

# Einzelne Binärdateien mit geprüfter SHA-256 (Werte aus den Release-Prüfsummen).
ARG GITLEAKS_VERSION=8.30.1
ARG GITLEAKS_SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
ARG ACTIONLINT_VERSION=1.7.12
ARG ACTIONLINT_SHA256=8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8
RUN set -eu; cd /tmp \
 && curl -fsSLo gitleaks.tar.gz "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
 && echo "${GITLEAKS_SHA256}  gitleaks.tar.gz" | sha256sum -c - \
 && tar -xzf gitleaks.tar.gz gitleaks && install -m 0755 gitleaks /usr/local/bin/gitleaks \
 && curl -fsSLo actionlint.tar.gz "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" \
 && echo "${ACTIONLINT_SHA256}  actionlint.tar.gz" | sha256sum -c - \
 && tar -xzf actionlint.tar.gz actionlint && install -m 0755 actionlint /usr/local/bin/actionlint \
 && rm -f /tmp/*.tar.gz /tmp/gitleaks /tmp/actionlint

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
