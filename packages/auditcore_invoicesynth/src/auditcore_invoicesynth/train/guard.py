"""Schutz gegen Hängen und stilles Scheitern eines Trainingslaufs.

* ``ProgressFile`` – ``<run-dir>/progress.json``, atomar (tmp + ``fsync`` +
  ``rename``) mit den Feldern des FlowAgent-Runners (``schritt``,
  ``schritte_gesamt``, ``epoche``, ``loss``, ``lr``, ``vram_mb``,
  ``gpu_temp_c``, ``zustand``, ``fehler``, ``letzter_checkpoint``,
  ``aktualisiert``). Während lang laufender Phasen (Modell laden, Checkpoint
  schreiben) hält ein Herzschlag ``aktualisiert`` frisch – begrenzt auf
  ``busy_limit_s``, damit ein echter Hänger trotzdem auffällt.
* ``StopRequest`` – SIGTERM/SIGINT setzen nur ein Flag; die Schleife schreibt
  nach dem laufenden Schritt einen Checkpoint und endet sauber. Ist das nicht
  binnen ``deadline_s`` geschehen, beendet ein Wächter den Prozess hart
  (Exit ``EXIT_STOP_TIMEOUT``).
* ``StepFailed`` – nicht endlicher Loss oder zu wenig Grafikspeicher. Der
  Schritt wird **vor** dem Optimiererschritt verworfen, der Zustand des
  letzten guten Schritts bleibt erhalten und wird gesichert.
"""

from __future__ import annotations

import json
import os
import signal
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signal import _HANDLER

PROGRESS = "progress.json"
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_NON_FINITE = 3
EXIT_OUT_OF_MEMORY = 4
EXIT_STOP_TIMEOUT = 5
EXIT_BAD_DATA = 6


class StepFailed(RuntimeError):
    """Schritt gescheitert; ``state_intact`` = Modellzustand entspricht dem Vorschritt."""

    exit_code = EXIT_FAILED

    def __init__(self, reason: str, *, state_intact: bool = True) -> None:
        super().__init__(reason)
        self.state_intact = state_intact


class NonFiniteLoss(StepFailed):
    """Loss ist NaN oder unendlich (kein Optimiererschritt ausgeführt)."""

    exit_code = EXIT_NON_FINITE


class OutOfMemory(StepFailed):
    """Grafikspeicher erschöpft (CUDA-OOM)."""

    exit_code = EXIT_OUT_OF_MEMORY


class TooManyBadSamples(StepFailed):
    """Zu viele unlesbare Beispiele – Datensatz beschädigt."""

    exit_code = EXIT_BAD_DATA


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class ProgressFile:
    """``progress.json`` atomar schreiben; Herzschlag nur in ``busy()``-Phasen."""

    def __init__(
        self,
        run_dir: Path,
        *,
        run_id: str,
        heartbeat_s: float = 30.0,
        busy_limit_s: float = 1800.0,
        now: Callable[[], str] = _now,
    ) -> None:
        self.path = Path(run_dir) / PROGRESS
        self.heartbeat_s = heartbeat_s
        self.busy_limit_s = busy_limit_s
        self.now = now
        self.state: dict[str, object] = {
            "run_id": run_id,
            "schritt": 0,
            "schritte_gesamt": None,
            "epoche": None,
            "loss": None,
            "lr": None,
            "vram_mb": None,
            "gpu_temp_c": None,
            "zustand": "startet",
            "phase": "start",
            "fehler": None,
            "letzter_checkpoint": None,
            "uebersprungene_beispiele": 0,
        }
        self._lock = threading.Lock()

    def update(self, **fields: object) -> None:
        with self._lock:
            self.state.update(fields)
            self._write()

    def _write(self) -> None:
        self.state["aktualisiert"] = self.now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{PROGRESS}.{os.getpid()}.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self.state, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    @contextmanager
    def busy(self, phase: str) -> Iterator[None]:
        """Phase ohne Schrittfortschritt: ``aktualisiert`` alle ``heartbeat_s`` erneuern."""
        previous = self.state.get("phase")
        self.update(phase=phase)
        done = threading.Event()
        started = time.monotonic()

        def beat() -> None:
            while not done.wait(self.heartbeat_s):
                if time.monotonic() - started > self.busy_limit_s:
                    return
                self.update()

        thread = threading.Thread(target=beat, name="progress-heartbeat", daemon=True)
        thread.start()
        try:
            yield
        finally:
            done.set()
            thread.join(timeout=5)
            self.update(phase=previous)


class StopRequest:
    """SIGTERM/SIGINT → ``requested``; nach ``deadline_s`` harter Abbruch."""

    def __init__(
        self,
        *,
        deadline_s: float = 90.0,
        on_timeout: Callable[[], None] | None = None,
        hard_exit: Callable[[int], None] = os._exit,
    ) -> None:
        self.deadline_s = deadline_s
        self.on_timeout = on_timeout
        self.hard_exit = hard_exit
        self.requested = False
        self.signal_name: str | None = None
        self._finished = threading.Event()
        self._previous: dict[int, _HANDLER] = {}

    def install(self) -> StopRequest:
        """Handler setzen (nur im Hauptthread möglich); ``finished`` stellt sie wieder her."""
        if threading.current_thread() is threading.main_thread():
            for number in (signal.SIGTERM, signal.SIGINT):
                self._previous[number] = signal.signal(number, self._handle)
        return self

    def _handle(self, signum: int, _frame: FrameType | None) -> None:
        self.trigger(signal.Signals(signum).name)

    def trigger(self, name: str = "SIGTERM") -> None:
        if self.requested:
            return
        self.requested = True
        self.signal_name = name
        threading.Thread(target=self._watch, name="stop-deadline", daemon=True).start()

    def _watch(self) -> None:
        if self._finished.wait(self.deadline_s):
            return
        if self.on_timeout is not None:
            self.on_timeout()
        self.hard_exit(EXIT_STOP_TIMEOUT)

    def finished(self) -> None:
        """Checkpoint geschrieben, Prozess endet regulär; frühere Handler zurück."""
        self._finished.set()
        for number, handler in self._previous.items():
            signal.signal(number, handler)
        self._previous.clear()

    def __call__(self) -> bool:
        return self.requested
