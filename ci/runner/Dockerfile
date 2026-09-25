# Ephemerer GitHub-Actions-Runner für die NUC.
# Basis: offizielles Runner-Image (MIT), per Digest fest gepinnt.
FROM ghcr.io/actions/actions-runner@sha256:e5496277be5d09bc968b3d64911b74e219ac4a3f2edce956a3ecf9271bea1ef4

USER root

# Systembibliotheken, die die auditcore-Tests auf ubuntu-latest vorfinden:
# Compiler für Wheels ohne Binärpaket, PDF-/Bild-Renderer (Pango, Cairo),
# XML, Schriften und deutsche Locale.
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

# Verzeichnisse für Werkzeug- und Paket-Cache vorab anlegen, damit Docker
# neue benannte Volumes mit den Rechten des Runner-Nutzers initialisiert.
RUN mkdir -p /home/runner/_work/_tool /home/runner/.cache /home/runner/.npm \
 && chown -R runner:runner /home/runner/_work /home/runner/.cache /home/runner/.npm \
 && gpasswd -d runner sudo && gpasswd -d runner docker \
 && rm -f /etc/sudoers.d/runner

USER runner
ENV RUNNER_TOOL_CACHE=/home/runner/_work/_tool \
    AGENT_TOOLSDIRECTORY=/home/runner/_work/_tool

ENTRYPOINT ["/bin/bash", "-c", "exec /home/runner/run.sh --jitconfig \"$AUDITCORE_JIT_CONFIG\""]
