#!/usr/bin/env bash
# auditcore-runner: Netzsperre für das Runner-Netz ${netz} (${subnetz}, Brücke ${bruecke}).
# Erzeugt von `auditcore-runner runner install`; braucht root.
#   sudo bash ${pfad} anwenden       Regeln setzen (idempotent) und Marker schreiben
#   sudo bash ${pfad} aktualisieren  nur die Egress-Allowlist neu auflösen (Zeitgeber)
#   sudo bash ${pfad} entfernen      Regeln, Allowlist und Marker entfernen
# Gesperrt nur für dieses Subnetz: private Netze (RFC 1918), CGNAT/Tailscale
# 100.64.0.0/10, Link-Local und der Host selbst. Mit Egress „allowlist“ sind
# außerdem nur die unten eingetragenen Ziele (aufgelöst in das ipset
# ${ipset}) auf den genannten TCP-Ports erreichbar; DNS läuft über den
# Docker-Resolver auf dem Host und ist davon nicht betroffen.
set -euo pipefail

SUBNET="${subnetz}"
BRIDGE="${bruecke}"
CHAIN="AUDITCORE-CI"
MARKER="/run/auditcore-ci-firewall.ok"
BLOCKED=(10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16)
EGRESS="${egress}"
EGRESS_SET="${ipset}"
EGRESS_PORTS="${egress_ports}"
EGRESS_HOSTS=(${egress_hosts})
EGRESS_META=(${egress_meta})

remove_rules() {
  iptables -D DOCKER-USER -s "$SUBNET" -j "$CHAIN" 2>/dev/null || true
  iptables -D INPUT -i "$BRIDGE" -j DROP 2>/dev/null || true
  iptables -D INPUT -i "$BRIDGE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
  iptables -F "$CHAIN" 2>/dev/null || true
  iptables -X "$CHAIN" 2>/dev/null || true
  rm -f "$MARKER"
}

add_resolved_hosts() {
  local host ip
  for host in "${EGRESS_HOSTS[@]}"; do
    while read -r ip; do
      ipset add "$1" "$ip" -exist && added=$((added + 1))
    done < <(getent ahostsv4 "$host" | awk '{print $1}' | sort -u)
  done
}

add_github_meta() {
  local meta key net
  (( ${#EGRESS_META[@]} )) || return 0
  meta="$(curl -fsS --max-time 30 https://api.github.com/meta)" || { echo "api.github.com/meta nicht erreichbar" >&2; return 0; }
  for key in "${EGRESS_META[@]}"; do
    while read -r net; do
      ipset add "$1" "$net" -exist && added=$((added + 1))
    done < <(jq -r --arg k "$key" '.[$k][]? | select(test(":") | not)' <<<"$meta")
  done
}

# Allowlist neu auflösen; eine leere Auflösung (Netz weg) ersetzt die alte nicht.
refresh_allowlist() {
  local fresh="$EGRESS_SET-neu"
  added=0
  ipset create "$EGRESS_SET" hash:net maxelem 262144 -exist
  ipset create "$fresh" hash:net maxelem 262144 -exist
  ipset flush "$fresh"
  add_resolved_hosts "$fresh"
  add_github_meta "$fresh"
  if (( added == 0 )); then
    ipset destroy "$fresh"
    echo "Allowlist nicht aufgelöst – bisherige bleibt." >&2
    return 0
  fi
  ipset swap "$fresh" "$EGRESS_SET"
  ipset destroy "$fresh"
  echo "Allowlist $EGRESS_SET: $added Einträge."
}

apply_rules() {
  remove_rules
  if [[ "$EGRESS" == "allowlist" ]]; then refresh_allowlist; fi
  iptables -N "$CHAIN"
  iptables -A "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  for net in "${BLOCKED[@]}"; do
    iptables -A "$CHAIN" -d "$net" -j REJECT --reject-with icmp-net-prohibited
  done
  if [[ "$EGRESS" == "allowlist" ]]; then
    iptables -A "$CHAIN" -p tcp -m multiport --dports "$EGRESS_PORTS" -m set --match-set "$EGRESS_SET" dst -j RETURN
    iptables -A "$CHAIN" -j REJECT --reject-with icmp-admin-prohibited
  fi
  iptables -A "$CHAIN" -j RETURN
  iptables -I DOCKER-USER 1 -s "$SUBNET" -j "$CHAIN"
  # Verkehr an den Host selbst (Gateway-Adresse, Host-Dienste) läuft über INPUT.
  iptables -I INPUT 1 -i "$BRIDGE" -j DROP
  iptables -I INPUT 1 -i "$BRIDGE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  install -m 0644 /dev/null "$MARKER"
  echo "Netzsperre für $SUBNET aktiv (Egress: $EGRESS)."
}

case "${1:-anwenden}" in
  anwenden) apply_rules ;;
  aktualisieren) if [[ "$EGRESS" == "allowlist" ]]; then refresh_allowlist; fi ;;
  entfernen)
    remove_rules
    ipset destroy "$EGRESS_SET" 2>/dev/null || true
    echo "Netzsperre entfernt."
    ;;
  *) echo "Aufruf: $0 anwenden|aktualisieren|entfernen" >&2; exit 2 ;;
esac
