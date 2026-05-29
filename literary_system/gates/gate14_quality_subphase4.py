"""
Gate 14: SubPhase 4 Quality Gate 핵심 모듈 생존 검증 (V450 신설)

검증 모듈:
  1. LLMJudge              — LLM-as-Judge 4축 평가기
  2. RubricCalibrator      — ADR-009 격주 캘리브레이션
  3. HallucinationDetector — 허상 탐지기
  4. SafetyGate            — 안전 게이트
  5. Gate9v2               — DRSE+Judge+Hallucination 통합 게이트
  6. Gate10v2              — 어댑터 계약 + Quality 모듈 생존 게이트
  7. ConsistencyChecker    — 씬 간 내러티브 일관성 검사
  8. ExternalConstraintMonitor — M-12 외부 제약 모니터
"""
from __future__ import annotations


def _gate_quality_subphase4_survival() -> dict:
    """SubPhase 4 Quality Gate 핵심 모듈 생존 검증."""
    try:
        # 1. LLMJudge
        from literary_system.quality.llm_judge import LLMJudge
        judge = LLMJudge(sampling_rate=1.0)
        class _R:
            trace_id = "t1"
            render_output = {"scene": "형사가 단서를 수집했다"}
            seed_contract = {"user_prompt": "씬을 써라"}
        score = judge.evaluate_one("t1", "씬을 써라", "형사가 단서를 수집했다", force=True)
        assert score is not None, "LLMJudge.evaluate_one() None 반환"

        # 2. RubricCalibrator (최소 10개 레코드 필요)
        from literary_system.quality.llm_judge import RubricCalibrator
        cal = RubricCalibrator(judge=judge)
        _recs10 = [type("_R", (), {
            "trace_id": f"cal{i}",
            "render_output": {"scene": f"형사 씬 {i}"},
            "seed_contract": {"user_prompt": f"씬 {i}을 써라"},
        })() for i in range(10)]
        run = cal.calibrate(_recs10, notes="gate14_test")
        assert hasattr(run, "drift_alarm"), "CalibrationRun.drift_alarm 없음"

        # 3. HallucinationDetector
        from literary_system.quality.hallucination_safety import HallucinationDetector
        det = HallucinationDetector()
        rep = det.detect("t_gate", "무해한 텍스트입니다.")
        assert not rep.flagged, "무해 텍스트가 허상으로 탐지됨"

        # 4. SafetyGate
        from literary_system.quality.hallucination_safety import SafetyGate
        gate = SafetyGate()
        res = gate.check("t_gate", "무해한 텍스트입니다.")
        assert not res.blocked, "무해 텍스트가 차단됨"

        # 5. Gate9v2
        from literary_system.gates.gate9_quality_v2 import Gate9v2
        g9 = Gate9v2()
        r9 = g9.run()
        assert hasattr(r9, "passed"), "Gate9v2Result.passed 없음"

        # 6. Gate10v2
        from literary_system.gates.gate10_quality_v2 import Gate10v2
        g10 = Gate10v2()
        r10 = g10.run(adapters=None)
        assert r10.quality_modules_passed, f"Gate10v2 quality 실패: {r10.reason}"

        # 7. ConsistencyChecker
        from literary_system.quality.consistency_checker import ConsistencyChecker
        class _CR:
            def __init__(self, i):
                self.trace_id = f"cr{i}"
                self.render_output = {"scene": f"씬 {i}"}
                self.metadata = {"episode_number": i}
        cc = ConsistencyChecker()
        cr = cc.check([_CR(1), _CR(2), _CR(3)])
        assert cr.consistent, f"ConsistencyChecker 일관성 실패: {cr.error_count} errors"

        # 8. ExternalConstraintMonitor
        from literary_system.quality.external_constraint_monitor import ExternalConstraintMonitor
        mon = ExternalConstraintMonitor()
        ecr = mon.check({"token_limit": 2000, "cost_budget": 0.5})
        assert ecr.passed, "ExternalConstraintMonitor 정상 수치에서 실패"

        return {
            "pass": True,
            "modules_verified": 8,
            "reason": "ok",
        }

    except Exception as e:
        import traceback
        return {
            "pass": False,
            "reason": f"gate14_exception: {e}",
            "traceback": traceback.format_exc(),
        }
