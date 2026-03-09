"""LangSmith integration helpers.

Fill these functions with real LangSmith SDK calls in implementation.
"""

from __future__ import annotations


def create_dataset_stub(name: str) -> dict:
    return {"dataset_name": name, "status": "stub"}
