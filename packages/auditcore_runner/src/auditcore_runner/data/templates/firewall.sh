#!/usr/bin/env bash
# auditcore-runner: Netzsperre für das Runner-Netz ${netz} (${subnetz}, Brücke ${bruecke}).
# Erzeugt von `auditcore-runner runner install`; braucht root.
#   sudo bash ${pfad} anwenden    Regeln setzen (idempotent) und Marker schreiben
#   sudo bash ${pfad} entfernen   Regeln und Marker entfernen
# Gesperrt nur für dieses Subnetz: private Netze (RFC 1918, u. a. LAN und
# WireGuard 10.77.0.0/24), Tailscale 100.64.0.0/10, Link-Local und der Host
# selbst. Internet und DNS über Docker bleiben erlaubt.
set -euo pipefail

SUBNET="${subnetz}"
BRIDGE="${bruecke}"
CHAIN="AUDITCORE-CI"
MARKER="/run/auditcore-ci-firewall.ok"
BLOCKED=(10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16)

remove_rules() {
  iptables -D DOCKER-USER -s "$SUBNET" -j "$CHAIN" 2>/dev/null || true
  iptables -D INPUT -i "$BRIDGE" -j DROP 2>/dev/null || true
  iptables -D INPUT -i "$BRIDGE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
  iptables -F "$CHAIN" 2>/dev/null || true
  iptables -X "$CHAIN" 2>/dev/null || true
  rm -f "$MARKER"
}

apply_rules() {
  remove_rules
  iptables -N "$CHAIN"
  iptables -A "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  for net in "${BLOCKED[@]}"; do
    iptables -A "$CHAIN" -d "$net" -j REJECT --reject-with icmp-net-prohibited
  done
  iptables -A "$CHAIN" -j RETURN
  iptables -I DOCKER-USER 1 -s "$SUBNET" -j "$CHAIN"
  # Verkehr an den Host selbst (Gateway-Adresse, Host-Dienste) läuft über INPUT.
  iptables -I INPUT 1 -i "$BRIDGE" -j DROP
  iptables -I INPUT 1 -i "$BRIDGE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  install -m 0644 /dev/null "$MARKER"
  echo "Netzsperre für $SUBNET aktiv."
}

case "${1:-anwenden}" in
  anwenden) apply_rules ;;
  entfernen) remove_rules; echo "Netzsperre entfernt." ;;
  *) echo "Aufruf: $0 anwenden|entfernen" >&2; exit 2 ;;
esac
