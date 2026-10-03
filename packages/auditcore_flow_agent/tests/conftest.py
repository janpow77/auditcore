from dataclasses import dataclass
from pathlib import Path

import pytest

from auditcore_flow_agent import Gpu, Node, Queue


@dataclass
class Clock:
    now: float = 1000

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def queue(tmp_path: Path, clock: Clock) -> Queue:
    result = Queue(tmp_path / "jobs.sqlite", clock=clock)
    result.publish_node(
        Node(
            "fast",
            clock(),
            8,
            32000,
            ("embed", "chat", "train", "image"),
            (Gpu("0", 16000), Gpu("1", 16000)),
            ("bge", "llm"),
            speed=10,
        )
    )
    result.publish_node(
        Node("fallback", clock(), 4, 8000, ("embed", "chat"), (Gpu("0", 8000),), ("bge",), speed=1)
    )
    return result
