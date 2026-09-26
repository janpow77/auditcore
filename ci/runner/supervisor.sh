#!/usr/bin/env bash
# Hält eine Runner-Instanz bereit: je Job ein frischer Container mit einer
# Einmal-Registrierung (JIT). Das GitHub-Token bleibt auf dem Host; der
# Container erhält nur die einmalig gültige JIT-Konfiguration.
set -euo pipefail

INSTANCE="${1:?Instanznummer fehlt}"
REPO="${AUDITCORE_RUNNER_REPO:-janpow77/auditcore}"
IMAGE="${AUDITCORE_RUNNER_IMAGE:-auditcore-runner:local}"
LABELS="${AUDITCORE_RUNNER_LABELS:-self-hosted,linux,x64,nuc,auditcore}"
CPUS="${AUDITCORE_RUNNER_CPUS:-2}"
MEMORY="${AUDITCORE_RUNNER_MEMORY:-6g}"
HOST="$(hostname -s)"

runner_id=""
container=""

cleanup() {
  if [[ -n "$container" ]]; then
    docker stop --time 20 "$container" >/dev/null 2>&1 || true
  fi
  if [[ -n "$runner_id" ]]; then
    gh api -X DELETE "repos/$REPO/actions/runners/$runner_id" >/dev/null 2>&1 || true
  fi
}
trap 'cleanup; exit 0' TERM INT

log() { printf '%s [runner %s] %s\n' "$(date -Is)" "$INSTANCE" "$*"; }

wait_for_prerequisites() {
  until docker info >/dev/null 2>&1 && gh api "repos/$REPO" --silent >/dev/null 2>&1; do
    log "warte auf Docker und GitHub-Erreichbarkeit"
    sleep 30
  done
}

request_jit_config() {
  local name="nuc-$HOST-$INSTANCE-$(date +%s)"
  local labels_json
  labels_json="$(jq -cn --arg l "$LABELS" '$l | split(",")')"
  jq -n --arg name "$name" --argjson labels "$labels_json" \
    '{name: $name, runner_group_id: 1, labels: $labels, work_folder: "_work"}' \
    | gh api -X POST "repos/$REPO/actions/runners/generate-jitconfig" --input -
}

run_one_job() {
  local response
  response="$(request_jit_config)"
  runner_id="$(jq -r '.runner.id' <<<"$response")"
  container="auditcore-runner-$INSTANCE-$runner_id"
  log "Runner $runner_id registriert, starte Container"
  AUDITCORE_JIT_CONFIG="$(jq -r '.encoded_jit_config' <<<"$response")" \
  docker run --rm --name "$container" \
    --env AUDITCORE_JIT_CONFIG \
    --cpus "$CPUS" --cpu-shares 512 --memory "$MEMORY" --pids-limit 4096 \
    --cap-drop ALL --security-opt no-new-privileges \
    --volume "auditcore-runner-tool-$INSTANCE:/home/runner/_work/_tool" \
    --volume "auditcore-runner-cache-$INSTANCE:/home/runner/.cache" \
    --volume "auditcore-runner-npm-$INSTANCE:/home/runner/.npm" \
    "$IMAGE" &
  wait $! || log "Container endete mit Fehler"
  container=""
  # Ephemere Runner entfernt GitHub nach dem Job selbst; das Löschen hier
  # räumt nur Registrierungen auf, die keinen Job bekommen haben.
  gh api -X DELETE "repos/$REPO/actions/runners/$runner_id" >/dev/null 2>&1 || true
  runner_id=""
}

while true; do
  wait_for_prerequisites
  if ! run_one_job; then
    log "Registrierung fehlgeschlagen, neuer Versuch in 60 s"
    sleep 60
  fi
  sleep 2
done
