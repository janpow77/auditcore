#!/usr/bin/env bash
# Installiert oder aktualisiert die NUC-Runner (idempotent, ohne sudo).
#   ci/runner/install.sh [ANZAHL]      Standard: 10 Instanzen
#   ci/runner/install.sh --uninstall   Runner stoppen und entfernen
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARE="$HOME/.local/share/auditcore-runner"
UNITS="$HOME/.config/systemd/user"
UNIT="auditcore-runner@.service"

active_instances() {
  systemctl --user list-units --all --plain --no-legend 'auditcore-runner@*.service' \
    | awk '{print $1}'
}

if [[ "${1:-}" == "--uninstall" ]]; then
  for unit in $(active_instances); do systemctl --user disable --now "$unit" || true; done
  rm -f "$UNITS/$UNIT"
  systemctl --user daemon-reload
  rm -rf "$SHARE"
  echo "Runner entfernt. Volumes bei Bedarf: docker volume ls | grep auditcore-runner"
  exit 0
fi

COUNT="${1:-10}"
command -v gh >/dev/null && gh auth status >/dev/null 2>&1 || { echo "gh ist nicht angemeldet"; exit 1; }
command -v jq >/dev/null || { echo "jq fehlt"; exit 1; }

docker build --pull -t auditcore-runner:local "$HERE"

install -d "$SHARE" "$UNITS"
install -m 0755 "$HERE/supervisor.sh" "$SHARE/supervisor.sh"
install -m 0644 "$HERE/systemd/$UNIT" "$UNITS/$UNIT"
systemctl --user daemon-reload

for unit in $(active_instances); do
  number="${unit#auditcore-runner@}"; number="${number%.service}"
  if (( number > COUNT )); then systemctl --user disable --now "$unit"; fi
done
for number in $(seq 1 "$COUNT"); do
  systemctl --user enable "auditcore-runner@$number.service" >/dev/null
  systemctl --user restart "auditcore-runner@$number.service"
done
echo "$COUNT Runner aktiv:"
systemctl --user --no-pager --plain list-units 'auditcore-runner@*.service'
