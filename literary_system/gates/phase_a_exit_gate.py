"""
phase_a_exit_gate.py — Phase A Exit Gate G52
SP-A.8 (V595) | ADR-055

6축 Phase A 완료 검증:
  EA-1  CLI import + 3 commands 존재
  EA-2  literary analyze — LOSConstitution score_scene_full 기능
  EA-3  literary generate — CorpusFallbackPipeline 기능
  EA-4  LOSConstitution v1.0 R(scene) >= 0.60 (단일 풍부 장면)
  EA-5  Phase A GATES count >= 51 + G51 PASS
  EA-6  테스트 총계 >= 6,000 (pytest --collect-only)

LLM-0 원칙: 외부 LLM 호출 0건
"""
from __future__ import annotations

import importlib
import inspect
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ---------------------------------------------------------------------------
# 공통 풍부 장면 텍스트 (G51과 동일한 _RICH_SCENE)
# ---------------------------------------------------------------------------
_RICH_SCENE = (
    "이도령과 춘향이 광한루에서 처음 만났다. 새로운 인연이 시작되었다. "
    '"이도령이라 하오." 이도령이 말했다. "저는 춘향입니다." 그녀가 답했다. '
    "이어서 두 사람은 이야기를 나눴다. 봄바람이 꽃잎을 날렸다. "
    "하지만 변학도의 갈등이 시작되었다. 위기와 대립이 고조되었다. "
    "마침내 이도령이 해결책을 찾아 돌아왔다. 결국 두 사람의 사랑이 승리했다. "
    "드디어 행복한 결말이 찾아왔다. "
)


# ---------------------------------------------------------------------------
# Gate G52 함수 (release_gate.py GATES 등록용)
# ---------------------------------------------------------------------------
def _gate_phase_a_exit_g52() -> dict:
    """
    Phase A Exit Gate G52: SP-A.8 Minimal-CLI + Phase A 6축 완료 검증.

    EA-1: CLI import + 3 commands (analyze/repair/generate)
    EA-2: score_scene_full() 5축 분해 기능
    EA-3: CorpusFallbackPipeline collect() 기능
    EA-4: R(scene) >= 0.60 — _RICH_SCENE 기준
    EA-5: GATES count >= 51 + constitution_g51 PASS
    EA-6: pytest --collect-only >= 6,000 테스트 수집
    """
    checks: dict = {}
    errors: list = []

    # ----- EA-1: CLI import + 3 commands -----
    try:
        from apps.cli.literary_cli import literary as cli_group
        commands = sorted(cli_group.commands.keys())
        ea1_ok = all(cmd in commands for cmd in ("analyze", "repair", "generate"))
        checks["EA-1"] = ea1_ok
        if not ea1_ok:
            errors.append(f"EA-1: commands={commands} (analyze/repair/generate 필요)")
    except Exception as e:
        checks["EA-1"] = False
        errors.append(f"EA-1 CLI import 실패: {e}")

    # ----- EA-2: score_scene_full() 5축 분해 -----
    try:
        from literary_system.constitution.los_constitution import LOSConstitution
        con = LOSConstitution()
        score = con.score_scene_full(_RICH_SCENE)
        ea2_ok = (
            hasattr(score, "drse") and hasattr(score, "debt")
            and hasattr(score, "arc") and hasattr(score, "tension")
            and hasattr(score, "prose") and hasattr(score, "total")
            and score.total >= 0.50
        )
        checks["EA-2"] = ea2_ok
        if not ea2_ok:
            errors.append(f"EA-2: total={score.total:.4f} 또는 축 누락")
    except Exception as e:
        checks["EA-2"] = False
        errors.append(f"EA-2 score_scene_full 실패: {e}")

    # ----- EA-3: CorpusFallbackPipeline.collect() -----
    try:
        from literary_system.corpus.corpus_ingestor import CorpusFallbackPipeline
        pipeline = CorpusFallbackPipeline(seed=0)
        entries = pipeline.collect(count=10)
        ea3_ok = len(entries) == 10 and all(len(e.text) > 0 for e in entries)
        checks["EA-3"] = ea3_ok
        if not ea3_ok:
            errors.append(f"EA-3: collect(10) → {len(entries)}개")
    except Exception as e:
        checks["EA-3"] = False
        errors.append(f"EA-3 pipeline.collect 실패: {e}")

    # ----- EA-4: R(scene) >= 0.60 (_RICH_SCENE) -----
    try:
        from literary_system.constitution.los_constitution import LOSConstitution
        con = LOSConstitution()
        score_val = con.score_scene(_RICH_SCENE)
        ea4_ok = score_val >= 0.60
        checks["EA-4"] = ea4_ok
        if not ea4_ok:
            errors.append(f"EA-4: R(scene)={score_val:.4f} < 0.60")
    except Exception as e:
        checks["EA-4"] = False
        errors.append(f"EA-4 score_scene 실패: {e}")

    # ----- EA-5: GATES >= 51 + constitution_g51 PASS -----
    try:
        from literary_system.gates.release_gate import GATES
        gate_count = len(GATES)

        # constitution_g51 직접 검증
        g51_fn = None
        for name, label, fn in GATES:
            if name == "constitution_g51":
                g51_fn = fn
                break

        g51_ok = False
        if g51_fn is not None:
            try:
                g51_result = g51_fn()
                # release_gate 함수는 "pass" 키 사용
                g51_ok = g51_result.get("pass", False)
            except Exception as ge:
                errors.append(f"EA-5 G51 실행 오류: {ge}")

        ea5_ok = gate_count >= 51 and g51_ok
        checks["EA-5"] = ea5_ok
        if not ea5_ok:
            errors.append(
                f"EA-5: GATES={gate_count} (>= 51 필요), G51={'PASS' if g51_ok else 'FAIL'}"
            )
    except Exception as e:
        checks["EA-5"] = False
        errors.append(f"EA-5 GATES 로드 실패: {e}")

    # ----- EA-6: test_inventory.json 읽기 + source_hash 검증 (FIX-D: V595.3) -----
    try:
        import json as _json
        import sys as _sys
        _repo_root = Path(__file__).resolve().parent.parent.parent
        _inventory_path = _repo_root / "tools" / "test_inventory.json"
        if not _inventory_path.exists():
            errors.append(
                "EA-6: test_inventory.json 없음 — "
                "python tools/generate_test_inventory.py 실행 필요"
            )
            checks["EA-6"] = False
        else:
            _inv = _json.loads(_inventory_path.read_text(encoding="utf-8"))
            test_count = _inv.get("test_count", 0)
            # FIX-D: source_hash 검증 — 재고 파일이 현재 소스와 일치하는지 확인
            if str(_repo_root) not in _sys.path:
                _sys.path.insert(0, str(_repo_root))
            try:
                from tools.generate_test_inventory import source_hash as _source_hash_fn
                _current_hash = _source_hash_fn()
                _inventory_hash = _inv.get("source_hash")
                if _inventory_hash != _current_hash:
                    errors.append(
                        f"EA-6: stale test_inventory.json "
                        f"(inventory={_inventory_hash}, current={_current_hash}) "
                        f"— python tools/generate_test_inventory.py 재실행 필요"
                    )
                    checks["EA-6"] = False
                elif test_count < 6000:
                    errors.append(
                        f"EA-6: test_count={test_count} (>= 6,000 필요) "
                        "— python tools/generate_test_inventory.py 재실행"
                    )
                    checks["EA-6"] = False
                else:
                    checks["EA-6"] = True
            except ImportError:
                # source_hash 임포트 불가 시 test_count만 검증 (하위 호환)
                if test_count < 6000:
                    errors.append(
                        f"EA-6: test_count={test_count} (>= 6,000 필요) "
                        "— python tools/generate_test_inventory.py 재실행"
                    )
                checks["EA-6"] = test_count >= 6000
    except Exception as e:
        errors.append(f"EA-6 test_inventory.json 읽기 실패: {e}")
        checks["EA-6"] = False

    passed = all(checks.values())
    passed_count = sum(1 for v in checks.values() if v)

    return {
        "gate_name": "Phase A Exit Gate G52 — Minimal-CLI + 6축 Phase A 완료",
        "pass": passed,
        "gate": "phase_a_exit_g52",
        "checkpoints": checks,
        "details": f"PhaseAExitGate {'PASS' if passed else 'FAIL'} — {passed_count}/6 체크포인트",
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# 직접 실행 지원
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    result = _gate_phase_a_exit_g52()
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    sys.exit(0 if result["pass"] else 1)
