"""Literary OS V381 런타임 스모크 테스트."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def run_smoke():
    results = {}
    # 핵심 모듈 import 검사
    checks = [
        ("V312Bridge",     "literary_system.compiler.v312_bridge",     "V312Bridge"),
        ("ProseContract",  "literary_system.prose.contract",            "ProseRenderContract"),
        ("SeriesArcPlanner","literary_system.arc",                      "SeriesArcPlanner"),
        ("RevealBudget",   "literary_system.ledgers.episode_reveal_budget", "EpisodeRevealBudget"),
        ("KnowledgeBridge","literary_system.world.character_knowledge_prose_bridge","CharacterKnowledgeProseBridge"),
        ("NKGGraphStore",  "literary_system.nkg.graph_store",           "NKGGraphStore"),
    ]
    for name, mod, cls in checks:
        try:
            m = __import__(mod, fromlist=[cls])
            getattr(m, cls)
            results[name] = "ok"
        except Exception as e:
            results[name] = f"FAIL: {e}"

    failed = [k for k, v in results.items() if v != "ok"]
    print(f"Smoke: {len(checks)-len(failed)}/{len(checks)} ok")
    for k, v in results.items():
        status = "✓" if v == "ok" else "✗"
        print(f"  {status} {k}: {v}")
    return {"status": "pass" if not failed else "fail", "results": results}

if __name__ == "__main__":
    import sys
    r = run_smoke()
    sys.exit(0 if r["status"] == "pass" else 1)
