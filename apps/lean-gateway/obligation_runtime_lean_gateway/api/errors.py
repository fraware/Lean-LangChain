from __future__ import annotations


def error_envelope(code: str, message: str, request_id: str = "req_local", details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id, "details": details or {}}}
