"""Worker isolation: timeout and resource limits for Lean invocations.

Current: in-process thread timeout only. Full isolation (container/microVM) is future work; see infra/README.md."""

from __future__ import annotations

import concurrent.futures
from typing import Callable, TypeVar

T = TypeVar("T")

DEFAULT_WALL_CLOCK_SECONDS = 300


def run_with_timeout(
    fn: Callable[[], T],
    timeout_seconds: float = DEFAULT_WALL_CLOCK_SECONDS,
) -> T:
    """Run fn in a thread with wall-clock limit. Raises TimeoutError on expiry."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn)
        try:
            return fut.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Run exceeded {timeout_seconds}s") from None
