#!/usr/bin/env bash
# Einmalig mit sudo ausführen: installiert die Netzsperre dauerhaft (systemd).
#   sudo bash ${pfad}
set -euo pipefail
install -m 0755 "${skript}" /usr/local/sbin/auditcore-ci-firewall
install -m 0644 "${unit}" /etc/systemd/system/auditcore-ci-firewall.service
systemctl daemon-reload
systemctl enable --now auditcore-ci-firewall.service
systemctl --no-pager status auditcore-ci-firewall.service | head -5
