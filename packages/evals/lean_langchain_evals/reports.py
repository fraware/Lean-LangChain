from __future__ import annotations


def summarize_results(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if all(v for k, v in r.items() if isinstance(v, bool)))
    return {"total": total, "passed": passed, "failed": total - passed}
