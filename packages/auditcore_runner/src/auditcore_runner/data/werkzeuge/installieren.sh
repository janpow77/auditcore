#!/usr/bin/env bash
# Installiert die Binär-Werkzeuge aus binaer.json nach /usr/local/bin (Node nach /opt/node).
# Jede Datei wird vor dem Entpacken gegen ihre SHA-256 geprüft; eine Abweichung bricht den Bau ab.
set -euo pipefail
liste="${1:-/tmp/werkzeuge/binaer.json}"
arbeit="$(mktemp -d)"
trap 'rm -rf "$arbeit"' EXIT

anzahl="$(jq '.werkzeuge | length' "$liste")"
for ((i = 0; i < anzahl; i++)); do
  eintrag="$(jq -c ".werkzeuge[$i]" "$liste")"
  name="$(jq -r .name <<<"$eintrag")"
  url="$(jq -r .url <<<"$eintrag")"
  sha="$(jq -r .sha256 <<<"$eintrag")"
  art="$(jq -r .art <<<"$eintrag")"
  datei="$(jq -r '.datei // empty' <<<"$eintrag")"
  ziel="$arbeit/$name.download"
  curl -fsSL --retry 5 --retry-delay 3 -o "$ziel" "$url"
  echo "$sha  $ziel" | sha256sum -c - >/dev/null
  case "$art" in
    binaer)
      install -m 0755 "$ziel" "/usr/local/bin/$name"
      ;;
    tar.gz)
      mkdir -p "$arbeit/$name"
      tar -xzf "$ziel" -C "$arbeit/$name" "$datei"
      install -m 0755 "$arbeit/$name/$datei" "/usr/local/bin/$name"
      ;;
    node)
      mkdir -p /opt/node
      tar -xJf "$ziel" -C /opt/node --strip-components=1
      for programm in node npm npx corepack; do ln -sf "/opt/node/bin/$programm" "/usr/local/bin/$programm"; done
      ;;
    *)
      echo "unbekannte Art '$art' für $name" >&2
      exit 1
      ;;
  esac
  echo "installiert: $name $(jq -r .version <<<"$eintrag")"
done
