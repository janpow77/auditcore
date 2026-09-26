#!/usr/bin/env bash
# Sizes the Vitest worker pool to the CPUs the job may actually use.
#
# The self-hosted runners are containers with a cgroup CPU quota (2 CPUs) on a
# 20-core host. Node 20 (libuv 1.46) ignores the quota and reports 20 CPUs, so
# Vitest starts 19 workers that fight over 2 CPUs; long parity tests then hit
# the 5 s timeout. Node 22 (libuv >= 1.49) already honours the quota. Writing
# VITEST_MAX_WORKERS to $GITHUB_ENV makes both versions behave the same; on
# hosted runners without a quota the result is the plain CPU count.
set -euo pipefail

cpus=$(nproc)
if [[ -r /sys/fs/cgroup/cpu.max ]]; then
  read -r quota period < /sys/fs/cgroup/cpu.max
  if [[ "$quota" != "max" && "$period" -gt 0 ]]; then
    limit=$(( quota / period ))
    (( limit < cpus )) && cpus=$limit
  fi
fi
(( cpus < 1 )) && cpus=1

echo "VITEST_MAX_WORKERS=$cpus"
if [[ -n "${GITHUB_ENV:-}" ]]; then
  echo "VITEST_MAX_WORKERS=$cpus" >> "$GITHUB_ENV"
fi
