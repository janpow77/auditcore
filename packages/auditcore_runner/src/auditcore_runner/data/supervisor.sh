#!/usr/bin/env bash
# auditcore-runner: hält eine Runner-Instanz bereit (aufgerufen von
# `auditcore-runner supervisor <klasse> <n>`). Je Job ein frischer Container
# mit einer Einmal-Registrierung (JIT). Das GitHub-Token bleibt auf dem Host.
#
# Vor jeder Registrierung werden Profil und Soll-Datei neu gelesen: Änderungen
# an Grenzen, Labels oder Soll wirken ab dem nächsten Job, ohne laufende Jobs
# abzubrechen. Überzählige Instanzen registrieren sich nicht mehr (Leerlauf).
# jq-Ausdrücke stehen bewusst in einfachen Anführungszeichen ($c, $g sind jq-Variablen).
# shellcheck disable=SC2016
set -euo pipefail

CLASS="${1:?Klasse fehlt}"
INSTANCE="${2:?Instanznummer fehlt}"
PROFILE="${AUDITCORE_RUNNER_PROFILE:?Profilpfad fehlt}"
POOL_FILE="${AUDITCORE_RUNNER_POOL:-}"
PROGRAM="${AUDITCORE_RUNNER_PROGRAM:-auditcore-runner}"
GPU_CLASS="${AUDITCORE_RUNNER_GPU_CLASS:-}"
GPU=""
FIREWALL_MARKER="${AUDITCORE_RUNNER_FIREWALL_MARKER:-/run/auditcore-ci-firewall.ok}"
SECRET_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/auditcore-runner"
HOST="$(hostname -s)"

runner_id=""
container=""
jit_file=""

log() { printf '%s [%s %s] %s\n' "$(date -Is)" "$CLASS" "$INSTANCE" "$*"; }

cfg() { jq -r --arg c "$CLASS" --arg g "$GPU" "$1" "$PROFILE"; }

# API-Pfad des Ziels: repos/<besitzer>/<repo> oder orgs/<organisation>.
repo() { cfg 'if .ziel.art == "org" then "orgs/" + .ziel.name else "repos/" + .ziel.name end'; }

# Token nur über das Paket (PAT-Datei oder GitHub App); bei „gh“ gilt gh auth.
load_token() {
  if [[ "$(cfg '.auth.art // "gh"')" != "gh" ]]; then
    GH_TOKEN="$("$PROGRAM" token)"
    export GH_TOKEN
  fi
}

cleanup() {
  if [[ -n "$container" ]]; then docker stop --time 20 "$container" >/dev/null 2>&1 || true; fi
  if [[ -n "$runner_id" ]]; then
    gh api -X DELETE "$(repo)/actions/runners/$runner_id" >/dev/null 2>&1 || true
  fi
  if [[ -n "$jit_file" ]]; then rm -f "$jit_file"; fi
}
trap 'cleanup; exit 0' TERM INT

# Darf diese Instanz jetzt einen Job annehmen? Klasse aktiv, Instanz ≤ Maximum,
# Instanz ≤ Soll des Reglers (falls vorhanden), GPU-Karte weiter erlaubt.
allowed() {
  local enabled maximum target
  enabled="$(cfg '.klassen[$c].aktiv // false')"
  maximum="$(cfg '.klassen[$c].max_instanzen // 0')"
  [[ "$enabled" == "true" ]] && (( INSTANCE <= maximum )) || return 1
  if [[ -n "$POOL_FILE" && -r "$POOL_FILE" ]]; then
    target="$(jq -r --arg c "$CLASS" '.klassen[$c].soll // empty' "$POOL_FILE" 2>/dev/null || true)"
    if [[ "$target" =~ ^[0-9]+$ ]] && (( INSTANCE > target )); then return 1; fi
  fi
}

# GPU-Klassen: die Karte wird je Job frisch gewählt (frei, VRAM reicht, Nutzer nicht darauf).
choose_gpu() {
  [[ -n "$GPU_CLASS" ]] || return 0
  GPU="$(flock "$SECRET_DIR/gpu.lock" "$PROGRAM" gpu waehlen "$CLASS" 2>/dev/null)" || { GPU=""; return 1; }
}

wait_until_allowed() {
  local said=0
  install -d -m 0700 "$SECRET_DIR"
  until allowed && choose_gpu; do
    if (( ! said )); then log "Instanz ruht (Klasse aus, über Maximum oder Soll)"; said=1; fi
    sleep 30
  done
  if (( said )); then log "Instanz wieder frei"; fi
}

wait_for_prerequisites() {
  load_token
  until docker info >/dev/null 2>&1 && gh api "$(repo)" --silent >/dev/null 2>&1; do
    log "warte auf Docker und GitHub-Erreichbarkeit"
    sleep 30
    load_token
  done
  if [[ "$(cfg '.netz.aktiv and .netz.sperre_pflicht')" == "true" ]]; then
    until [[ -e "$FIREWALL_MARKER" ]]; do
      log "warte auf die Netzsperre (auditcore-ci-firewall.service)"
      sleep 30
    done
  fi
}

request_jit_config() {
  local name labels
  name="$(cfg '.rechner')-$HOST-$CLASS-$INSTANCE-$(date +%s)"
  labels="$(cfg '.klassen[$c].labels')"
  jq -n --arg name "$name" --argjson labels "$labels" \
    --argjson group "$(cfg '.ziel.runner_gruppe // 1')" \
    '{name: $name, runner_group_id: $group, labels: $labels, work_folder: "_work"}' \
    | gh api -X POST "$(repo)/actions/runners/generate-jitconfig" --input -
}

# Sinkt Soll oder Maximum, während die Registrierung noch auf einen Job wartet,
# wird sie gelöscht und der leere Container beendet. Einen belegten Runner lehnt
# GitHub beim Löschen ab; dann läuft der Job normal zu Ende.
watch_allowed() {
  local id="$1" name="$2"
  while docker inspect "$name" >/dev/null 2>&1; do
    sleep 20
    # Nutzer-Vorrang: Karte sofort räumen, auch mitten im Job (der Workflow stößt ihn neu an).
    if [[ -n "$GPU" ]] && ! "$PROGRAM" gpu pruefen "$GPU" >/dev/null 2>&1; then
      log "Nutzer braucht $GPU – Container wird geräumt"
      docker stop --time 20 "$name" >/dev/null 2>&1 || true
      return
    fi
    if ! allowed \
      && [[ "$(gh api "$(repo)/actions/runners/$id" -q .busy 2>/dev/null)" == "false" ]] \
      && gh api -X DELETE "$(repo)/actions/runners/$id" >/dev/null 2>&1; then
      log "unbenutzte Registrierung $id entfernt"
      docker stop --time 5 "$name" >/dev/null 2>&1 || true
      return
    fi
  done
}

container_args() {
  local network volume shares
  shares="$(cfg '.klassen[$c].cpu_shares')"
  args=(
    --rm --name "$container"
    --volume "$jit_file:/run/auditcore/jit:ro"
    --cpus "$(cfg '.klassen[$c].cpus')" --cpu-shares "$shares"
    --memory "$(cfg '.klassen[$c].speicher_gb')g" --pids-limit 4096
    --cap-drop ALL --security-opt no-new-privileges
    --label "auditcore-runner.klasse=$CLASS"
    --volume "auditcore-runner-tool-$CLASS-$INSTANCE:/home/runner/_work/_tool"
    --volume "auditcore-runner-cache-$CLASS-$INSTANCE:/home/runner/.cache"
    --volume "auditcore-runner-npm-$CLASS-$INSTANCE:/home/runner/.npm"
  )
  network="$(cfg 'if .netz.aktiv then .netz.name else "" end')"
  if [[ -n "$network" ]]; then args+=(--network "$network"); fi
  volume="$(cfg '.klassen[$c].uv_cache_volume // ""')"
  if [[ -n "$volume" ]]; then
    args+=(--volume "$volume:/home/runner/.cache/uv" --env UV_CACHE_DIR=/home/runner/.cache/uv)
  fi
  if [[ -n "$GPU" ]]; then
    args+=(--gpus "\"device=$GPU\"" --env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True)
    args+=(--label "auditcore-runner.gpu=$GPU")
  fi
}

run_one_job() {
  local response watcher job
  response="$(request_jit_config)"
  runner_id="$(jq -r '.runner.id' <<<"$response")"
  container="auditcore-runner-$CLASS-$INSTANCE-$runner_id"
  install -d -m 0700 "$SECRET_DIR"
  jit_file="$SECRET_DIR/jit-$CLASS-$INSTANCE"
  # Die JIT-Konfiguration liegt als Datei auf tmpfs (Verzeichnis 0700) und wird
  # eingebunden – nicht als Umgebungsvariable, damit sie nicht in `docker inspect` steht.
  (umask 022; jq -r '.encoded_jit_config' <<<"$response" >"$jit_file")
  container_args
  log "Runner $runner_id registriert, starte Container"
  docker run "${args[@]}" "$(cfg '.image')" &
  job=$!
  watch_allowed "$runner_id" "$container" &
  watcher=$!
  wait "$job" || log "Container endete mit Fehler"
  kill "$watcher" 2>/dev/null || true
  container=""
  rm -f "$jit_file"
  jit_file=""
  gh api -X DELETE "$(repo)/actions/runners/$runner_id" >/dev/null 2>&1 || true
  runner_id=""
  GPU=""
}

while true; do
  wait_for_prerequisites
  wait_until_allowed
  if ! run_one_job; then
    log "Registrierung fehlgeschlagen, neuer Versuch in 60 s"
    sleep 60
  fi
  sleep 2
done
