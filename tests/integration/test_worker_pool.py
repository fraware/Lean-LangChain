from pathlib import Path

from lean_langchain_gateway.server.worker_pool import WorkerPool


def test_worker_pool_reuses_fingerprint_worker(tmp_path: Path) -> None:
    pool = WorkerPool()
    a = pool.acquire("fp1", tmp_path)
    b = pool.acquire("fp1", tmp_path)
    assert a.worker_id == b.worker_id
