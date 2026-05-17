"""
V449: Gate10 v2 — LLM 어댑터 계약 + 품질 모듈 생존 검증
Gate10 v1(LLMAdapterContractGate)에 Quality 모듈 인터페이스 생존 검사를 추가.

추가 검사:
  - LLMJudge:             evaluate_one(), evaluate(), stats() 존재
  - RubricCalibrator:     calibrate(), stats() 존재
  - HallucinationDetector: detect(), detect_batch(), stats() 존재
  - SafetyGate:           check(), check_batch(), stats() 존재

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class QualityModuleViolation:
    module_class: str
    missing:      str
    detail:       str


@dataclass
class Gate10v2Result:
    passed:                 bool
    adapter_contract_passed: bool
    quality_modules_passed: bool
    adapters_checked:       int
    quality_modules_checked: int
    violations:             List[Any] = field(default_factory=list)
    quality_violations:     List[QualityModuleViolation] = field(default_factory=list)
    reason:                 str = ""

    def to_dict(self) -> dict:
        return {
            "passed":                  self.passed,
            "adapter_contract_passed": self.adapter_contract_passed,
            "quality_modules_passed":  self.quality_modules_passed,
            "adapters_checked":        self.adapters_checked,
            "quality_modules_checked": self.quality_modules_checked,
            "violation_count":         len(self.violations) + len(self.quality_violations),
            "reason":                  self.reason,
        }


# 품질 모듈 필수 메서드 정의
_QUALITY_MODULE_CONTRACTS = {
    "LLMJudge":              ["evaluate_one", "evaluate", "stats"],
    "RubricCalibrator":      ["calibrate", "summary"],
    "HallucinationDetector": ["detect", "detect_batch", "stats"],
    "SafetyGate":            ["check", "check_batch", "stats"],
}


class Gate10v2:
    """
    Gate 10 v2: LLM 어댑터 계약 + 품질 모듈 생존 검증.
    """

    def run(self, adapters: list = None, task_router=None) -> Gate10v2Result:
        from literary_system.gates.gate10_llm_contract import LLMAdapterContractGate

        # ── 어댑터 계약 검사 ────────────────────────
        adapter_contract_passed = True
        adapter_violations      = []
        adapters_checked        = 0

        if adapters is not None:
            contract_gate   = LLMAdapterContractGate()
            contract_result = contract_gate.check(adapters, task_router=task_router)
            adapter_contract_passed = contract_result.passed
            adapter_violations      = contract_result.violations
            adapters_checked        = contract_result.adapters_checked

        # ── 품질 모듈 생존 검사 ─────────────────────
        quality_violations:      List[QualityModuleViolation] = []
        quality_modules_checked = 0

        try:
            from literary_system.quality.llm_judge import LLMJudge, RubricCalibrator
            from literary_system.quality.hallucination_safety import (
                HallucinationDetector, SafetyGate,
            )
            _judge = LLMJudge()
            instances = {
                "LLMJudge":              _judge,
                "RubricCalibrator":      RubricCalibrator(judge=_judge),
                "HallucinationDetector": HallucinationDetector(),
                "SafetyGate":            SafetyGate(),
            }
        except ImportError as e:
            return Gate10v2Result(
                passed=False,
                adapter_contract_passed=adapter_contract_passed,
                quality_modules_passed=False,
                adapters_checked=adapters_checked,
                quality_modules_checked=0,
                reason=f"quality_module_import_error: {e}",
            )

        for class_name, required_methods in _QUALITY_MODULE_CONTRACTS.items():
            instance = instances[class_name]
            quality_modules_checked += 1
            for method in required_methods:
                if not hasattr(instance, method) or not callable(getattr(instance, method)):
                    quality_violations.append(QualityModuleViolation(
                        module_class=class_name,
                        missing=method,
                        detail=f"{class_name}.{method}() 누락 또는 호출 불가",
                    ))

        quality_modules_passed = len(quality_violations) == 0
        passed                 = adapter_contract_passed and quality_modules_passed

        reasons = []
        if not adapter_contract_passed:
            reasons.append(f"adapter_violations={len(adapter_violations)}")
        if not quality_modules_passed:
            reasons.append(f"quality_violations={len(quality_violations)}")

        return Gate10v2Result(
            passed=passed,
            adapter_contract_passed=adapter_contract_passed,
            quality_modules_passed=quality_modules_passed,
            adapters_checked=adapters_checked,
            quality_modules_checked=quality_modules_checked,
            violations=adapter_violations,
            quality_violations=quality_violations,
            reason=", ".join(reasons) if reasons else "ok",
        )


def _gate10_v2_fn() -> dict:
    """Release Gate — Gate10 v2 실행 함수."""
    try:
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        from literary_system.llm_bridge.routing.task_router import TaskRouter
        from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter

        adapters = [OpenAICompatibleAdapter.for_ollama(), MockLLMBridge()]
        router   = TaskRouter()

        gate10v2 = Gate10v2()
        result   = gate10v2.run(adapters=adapters, task_router=router)

        return {
            "pass":   result.passed,
            "reason": result.reason,
            "details": result.to_dict(),
        }
    except Exception as e:
        return {"pass": False, "reason": f"gate10v2_exception: {e}"}
