from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(payload: Any) -> str:
    raw = canonical_dumps(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
