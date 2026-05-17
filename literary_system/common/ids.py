from __future__ import annotations

from itertools import count

_COUNTERS: dict[str, count] = {}


def make_id(prefix: str) -> str:
    if prefix not in _COUNTERS:
        _COUNTERS[prefix] = count(1)
    return f"{prefix}_{next(_COUNTERS[prefix]):04d}"
