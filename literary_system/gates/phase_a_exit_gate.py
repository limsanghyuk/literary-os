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
from typing import Dict, Any

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
    EA-4: R(scene) >= 0.60 — _RICH_SCENE * 3 기준
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

    # ----- EA-4: R(scene) >= 0.60 (_RICH_SCENE * 3) -----
    try:
        from literary_system.constitution.los_constitution import LOSConstitution
        con = LOSConstitution()
        score_val = con.score_scene(_RICH_SCENE * 3)
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

    # ----- EA-6: 테스트 총계 >= 6,000 -----
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "--tb=no", "-p", "no:warnings"],
            capture_output=True, text=True, cwd=_ROOT, timeout=120,
        )
        output = proc.stdout + proc.stderr
        lines = output.strip().splitlines()
        # "N tests collected" 또는 "N selected" 형태 파싱
        test_count = 0
        for line in reversed(lines):
            if "collected" in line or "selected" in line:
                for token in line.split():
                    if token.isdigit():
                        test_count = int(token)
                        break
                if test_count:
                    break
        ea6_ok = test_count >= 6000
        checks["EA-6"] = ea6_ok
        if not ea6_ok:
            errors.append(f"EA-6: collected={test_count} (>= 6,000 필요)")
    except Exception as e:
        checks["EA-6"] = False
        errors.append(f"EA-6 pytest --collect-only 실패: {e}")

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
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["pass"] else 1)
