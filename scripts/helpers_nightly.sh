#!/usr/bin/env bash
# Nächtlicher Lauf von auditcore-helpers über alle App-Repositorys der NUC.
#
# Nur lesend: Die App-Repositorys werden weder verändert noch umgeschaltet
# (kein Schreiben der Baseline, Python läuft mit -B, keine .pyc-Dateien). Der
# auditcore-Stand kommt per "git archive" aus origin/main; der Checkout unter
# $AUDITCORE_ROOT bleibt auf seinem Zweig.
#
# Einschalten (ein Befehl, installiert Skript und systemd-User-Timer):
#   git -C ~/Projekte/auditcore fetch origin && \
#     git -C ~/Projekte/auditcore show origin/main:scripts/helpers_nightly.sh | bash -s -- --enable
# Ausschalten:
#   systemctl --user disable --now auditcore-helpers-nightly.timer
#
# Umgebung (optional): HELPERS_PROJECTS_DIR, AUDITCORE_ROOT, HELPERS_REPOS
# (Leerzeichen-getrennte Auswahl), HELPERS_EXCLUDE, HELPERS_STATE_DIR,
# HELPERS_AUDITCORE_REF, HELPERS_TIMEOUT (Sekunden je Repository).
set -euo pipefail

PROJECTS_DIR="${HELPERS_PROJECTS_DIR:-$HOME/Projekte}"
AUDITCORE_ROOT="${AUDITCORE_ROOT:-$PROJECTS_DIR/auditcore}"
STATE_DIR="${HELPERS_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/auditcore/helpers-nightly}"
REF="${HELPERS_AUDITCORE_REF:-origin/main}"
EXCLUDE="${HELPERS_EXCLUDE:-auditcore}"
SELECTED="${HELPERS_REPOS:-}"
TIMEOUT="${HELPERS_TIMEOUT:-1800}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/auditcore"
UNIT=auditcore-helpers-nightly

enable_timer() {
  git -C "$AUDITCORE_ROOT" fetch --quiet origin || echo "WARN: git fetch fehlgeschlagen, nutze lokalen Stand von $REF"
  mkdir -p "$UNIT_DIR" "$INSTALL_DIR"
  git -C "$AUDITCORE_ROOT" show "$REF:scripts/helpers_nightly.sh" > "$INSTALL_DIR/helpers_nightly.sh"
  chmod +x "$INSTALL_DIR/helpers_nightly.sh"
  for suffix in service timer; do
    git -C "$AUDITCORE_ROOT" show "$REF:scripts/systemd/$UNIT.$suffix" > "$UNIT_DIR/$UNIT.$suffix"
  done
  systemctl --user daemon-reload
  systemctl --user enable --now "$UNIT.timer"
  systemctl --user list-timers "$UNIT.timer" --no-pager
}

prepare_tool() {
  git -C "$AUDITCORE_ROOT" fetch --quiet origin || echo "WARN: git fetch fehlgeschlagen, nutze lokalen Stand von $REF"
  SOURCE="$STATE_DIR/auditcore-src"
  rm -rf "$SOURCE" && mkdir -p "$SOURCE"
  git -C "$AUDITCORE_ROOT" archive "$REF" | tar -x -C "$SOURCE"
  VENV="$STATE_DIR/venv"
  [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet --upgrade --force-reinstall --no-deps "$SOURCE"
  "$VENV/bin/auditcore-helpers" toolchain > /dev/null
}

selected() {
  local name="$1"
  [[ "$name" == *-wt ]] && return 1
  case " $EXCLUDE " in *" $name "*) return 1 ;; esac
  [ -z "$SELECTED" ] && return 0
  case " $SELECTED " in *" $name "*) return 0 ;; esac
  return 1
}

run_repo() {
  local dir="$1" name="$2" out="$3"
  local args=(check "$dir" --no-fail --cases "$SOURCE/contracts/common-cases" --library-root "$SOURCE"
              --output "$out/$name.json" --markdown "$out/$name.md")
  if ! timeout "$TIMEOUT" "$VENV/bin/auditcore-helpers" "${args[@]}" > "$out/$name.log" 2>&1; then
    echo "| $name | NICHT AUSFÜHRBAR | – | – | – | siehe $name.log |" >> "$out/INDEX.md"
    return 0
  fi
  "$VENV/bin/python" - "$out/$name.json" "$name" >> "$out/INDEX.md" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
scan = report.get("scan", {})
library = sum(1 for m in scan.get("library_matches", []) if m.get("status") == "vorhanden")
lint = len(report.get("lint", {}).get("findings", []))
violations = sum(len(run.get("violations", [])) for run in report.get("contracts", []))
ratchet = report.get("ratchet", {})
verdicts = ratchet.get("verdicts", [])
new = sum(1 for v in verdicts if v.get("message", "").startswith("neu"))
fixed = sum(1 for v in verdicts if v.get("message", "").startswith("behoben"))
status = ratchet.get("status")
if any(v.get("message", "").startswith("Keine Baseline") for v in verdicts):
    status = "keine Baseline"
print(f"| {sys.argv[2]} | {status} | {library} | {lint} | {violations} | {new} neu, {fixed} behoben |")
PY
}

main() {
  if [ "${1:-}" = "--enable" ]; then
    enable_timer
    return
  fi
  mkdir -p "$STATE_DIR"
  local out="$STATE_DIR/$(date +%F)"
  mkdir -p "$out"
  prepare_tool
  {
    echo "# Helfer-Verträge, nächtlicher Lauf $(date '+%d.%m.%Y %H:%M')"
    echo
    echo "auditcore $REF @ $(git -C "$AUDITCORE_ROOT" rev-parse --short "$REF")"
    echo
    echo "| Repository | Ratchet | Bibliotheks-Duplikate | Lint-Befunde | Vertragsverletzungen | Neu ggü. Baseline |"
    echo "|---|---|---:|---:|---:|---|"
  } > "$out/INDEX.md"
  export PYTHONDONTWRITEBYTECODE=1
  for dir in "$PROJECTS_DIR"/*/; do
    local name
    name="$(basename "$dir")"
    [ -d "$dir/.git" ] || [ -f "$dir/.git" ] || continue
    selected "$name" || continue
    run_repo "${dir%/}" "$name" "$out"
  done
  ln -sfn "$out" "$STATE_DIR/latest"
  echo "Bericht: $out/INDEX.md"
}

main "$@"
