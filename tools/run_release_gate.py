"""Literary OS V381 릴리스 게이트 실행 스크립트."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from literary_system.gates.release_gate import run_release_gate

if __name__ == "__main__":
    result = run_release_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "pass" else 1)
