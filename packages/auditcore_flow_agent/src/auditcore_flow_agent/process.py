"""POSIX-Prozesswächter mit absolutem Zeitlimit und begrenzter Ausgabepufferung.

Die Prozessgruppe gehört vollständig zum Auftrag. Container und entfernte
Modellaufrufe benötigen eigene Adapter zum bestätigten Stoppen.
"""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from .validation import integer, positive


@dataclass(frozen=True)
class Command:
    argv: tuple[str, ...]
    cwd: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple) or not self.argv or not self.argv[0]:
            raise ValueError("Ein Programm mit Argumentliste ist erforderlich.")
        if not all(isinstance(arg, str) and "\x00" not in arg for arg in self.argv):
            raise ValueError("Programmargumente müssen Text ohne Nullzeichen sein.")


@dataclass(frozen=True)
class ProcessResult:
    returncode: int | None
    reason: str
    elapsed_s: float
    stdout_tail: str
    stderr_tail: str


class ProcessNotStopped(RuntimeError):
    """Prozessende ist nicht nachgewiesen; zugehörige Ressourcen bleiben gesperrt."""


def _signal_group(pid: int, signum: int) -> None:
    with suppress(ProcessLookupError):
        os.killpg(pid, signum)


def _stop(process: subprocess.Popen[bytes], grace_s: float) -> None:
    _signal_group(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # Auch noch lebende Kinder beenden, wenn der direkte Prozess bereits ausstieg.
        _signal_group(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=grace_s)
        except subprocess.TimeoutExpired as error:
            raise ProcessNotStopped("Prozessende nach SIGKILL nicht bestätigt.") from error


class _Output:
    def __init__(self, streams: tuple[IO[bytes], IO[bytes]], limit: int) -> None:
        self.selector = selectors.DefaultSelector()
        self.limit = limit
        self.tails = [bytearray(), bytearray()]
        self.streams = streams
        for index, stream in enumerate(streams):
            self.selector.register(stream, selectors.EVENT_READ, index)

    def read(self, wait_s: float) -> None:
        for key, _ in self.selector.select(wait_s):
            block = os.read(key.fd, 65536)
            if not block:
                self.selector.unregister(key.fileobj)
                continue
            tail = self.tails[key.data]
            tail.extend(block)
            del tail[: -self.limit]

    def close(self) -> None:
        self.selector.close()
        for stream in self.streams:
            stream.close()

    def drain(self, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        while self.selector.get_map():
            if time.monotonic() >= deadline:
                raise ProcessNotStopped("Ausgabekanäle bleiben nach Prozessende offen.")
            self.read(0.01)

    def text(self, index: int) -> str:
        return self.tails[index].decode("utf-8", errors="replace")


def _watch(
    process: subprocess.Popen[bytes],
    output: _Output,
    started: float,
    timeout_s: float,
    tick: Callable[[], bool],
    poll_s: float,
) -> str:
    while process.poll() is None:
        if time.monotonic() - started >= timeout_s:
            return "timeout"
        if not tick():
            return "lease_lost"
        output.read(poll_s)
        # Geschlossene Ausgabekanäle dürfen keine CPU-Endlosschleife verursachen.
        if not output.selector.get_map():
            time.sleep(poll_s)
    return "exited"


def run_command(
    command: Command,
    *,
    timeout_s: float,
    tick: Callable[[], bool] = lambda: True,
    poll_s: float = 0.1,
    stop_grace_s: float = 1,
    output_limit: int = 16384,
) -> ProcessResult:
    """Programm ohne Shell ausführen; bei Fehlern immer die Prozessgruppe aufräumen.

    ``tick`` muss selbst eine kurze, begrenzte Laufzeit haben. Die Uhr läuft
    monoton; tick/Queue-Lebenszeichen können das absolute Zeitlimit nicht ändern.
    """
    if os.name != "posix":
        raise NotImplementedError("Der Prozesswächter benötigt POSIX-Prozessgruppen.")
    for name, value in (
        ("timeout_s", timeout_s),
        ("poll_s", poll_s),
        ("stop_grace_s", stop_grace_s),
    ):
        positive(value, name)
    integer(output_limit, "output_limit", minimum=1)
    started = time.monotonic()
    if not tick():
        return ProcessResult(None, "lease_lost", 0, "", "")
    process = subprocess.Popen(
        command.argv,
        cwd=command.cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stderr is not None
    output = _Output((process.stdout, process.stderr), output_limit)
    try:
        reason = _watch(process, output, started, timeout_s, tick, poll_s)
        _stop(process, stop_grace_s)
        output.drain(stop_grace_s)
        return ProcessResult(
            process.returncode, reason, time.monotonic() - started, output.text(0), output.text(1)
        )
    finally:
        try:
            _stop(process, stop_grace_s)
        finally:
            output.close()
