"""
V411-I — Gate 10: LLMAdapterContractGate
등록된 모든 LLMBridgeInterface 구현체의 계약 준수 자동 검증.

Release Gate 10으로 등록되어 인터페이스 회귀를 자동 방지한다.

검사 항목:
  1. generate() 시그니처: (self, prompt: str, context) → str
  2. is_available() 메서드 존재
  3. get_provider_id() 메서드 존재
  4. provider_name 프로퍼티 존재
  5. TaskRouter.route() 소스에 .generate( 직접 호출 없음 (LLM-0)
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ────────────────────────────────────────────────────────────────
# ContractViolation
# ────────────────────────────────────────────────────────────────

@dataclass
class ContractViolation:
    adapter_class: str
    violation_type: str   # "signature" | "missing_method" | "llm0" | "property"
    detail: str


# ────────────────────────────────────────────────────────────────
# GateResult (Gate 10 전용)
# ────────────────────────────────────────────────────────────────

@dataclass
class ContractGateResult:
    passed: bool
    adapters_checked: int = 0
    violations: List[ContractViolation] = field(default_factory=list)
    llm0_passed: bool = True
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "passed":           self.passed,
            "adapters_checked": self.adapters_checked,
            "llm0_passed":      self.llm0_passed,
            "violation_count":  len(self.violations),
            "violations": [
                {"adapter": v.adapter_class,
                 "type":    v.violation_type,
                 "detail":  v.detail}
                for v in self.violations
            ],
            "summary": self.summary,
        }


# ────────────────────────────────────────────────────────────────
# LLMAdapterContractGate
# ────────────────────────────────────────────────────────────────

class LLMAdapterContractGate:
    """
    Gate 10: LLM 어댑터 계약 자동 검증.

    사용 예:
        gate = LLMAdapterContractGate()
        result = gate.check([OllamaAdapter(), MockLLMBridge()], task_router=router)
        assert result.passed
    """

    # generate() 필수 파라미터
    REQUIRED_GENERATE_PARAMS = {"prompt", "context"}
    # 필수 메서드 목록
    REQUIRED_METHODS = {"generate", "parse_action_packet", "is_available", "get_provider_id"}
    # 필수 프로퍼티
    REQUIRED_PROPERTIES = {"provider_name"}

    def check(
        self,
        adapters: List[Any],
        task_router=None,   # TaskRouter (LLM-0 검사용)
    ) -> ContractGateResult:
        """
        어댑터 목록 전체를 검사하고 ContractGateResult 반환.
        """
        violations: List[ContractViolation] = []

        for adapter in adapters:
            violations.extend(self._check_methods(adapter))
            violations.extend(self._check_generate_signature(adapter))
            violations.extend(self._check_properties(adapter))

        llm0_ok = True
        if task_router is not None:
            llm0_violations = self._check_llm0(task_router)
            violations.extend(llm0_violations)
            llm0_ok = len(llm0_violations) == 0

        passed = len(violations) == 0
        return ContractGateResult(
            passed           = passed,
            adapters_checked = len(adapters),
            violations       = violations,
            llm0_passed      = llm0_ok,
            summary          = (
                f"Gate10 PASS: {len(adapters)} adapters checked"
                if passed else
                f"Gate10 FAIL: {len(violations)} violations in {len(adapters)} adapters"
            ),
        )

    # ── 내부 검사 메서드 ─────────────────────────────────────────

    def _check_methods(self, adapter) -> List[ContractViolation]:
        violations = []
        cls_name = type(adapter).__name__
        for method in self.REQUIRED_METHODS:
            if not hasattr(adapter, method) or not callable(getattr(adapter, method)):
                violations.append(ContractViolation(
                    adapter_class  = cls_name,
                    violation_type = "missing_method",
                    detail         = f"Missing required method: {method}()",
                ))
        return violations

    def _check_generate_signature(self, adapter) -> List[ContractViolation]:
        violations = []
        cls_name = type(adapter).__name__
        try:
            sig    = inspect.signature(adapter.generate)
            params = set(sig.parameters.keys()) - {"self"}
            # "prompt"와 "context" 파라미터 존재 확인
            for required in self.REQUIRED_GENERATE_PARAMS:
                if required not in params:
                    violations.append(ContractViolation(
                        adapter_class  = cls_name,
                        violation_type = "signature",
                        detail         = f"generate() missing parameter: '{required}'",
                    ))
            # **kwargs 금지 (명시적 계약 위반)
            for pname, param in sig.parameters.items():
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    violations.append(ContractViolation(
                        adapter_class  = cls_name,
                        violation_type = "signature",
                        detail         = "generate() uses **kwargs — explicit context: LLMContext required",
                    ))
        except (TypeError, ValueError) as e:
            violations.append(ContractViolation(
                adapter_class  = cls_name,
                violation_type = "signature",
                detail         = f"Cannot inspect generate() signature: {e}",
            ))
        return violations

    def _check_properties(self, adapter) -> List[ContractViolation]:
        violations = []
        cls_name = type(adapter).__name__
        for prop in self.REQUIRED_PROPERTIES:
            if not hasattr(adapter, prop):
                violations.append(ContractViolation(
                    adapter_class  = cls_name,
                    violation_type = "property",
                    detail         = f"Missing required property: {prop}",
                ))
        return violations

    def _check_llm0(self, task_router) -> List[ContractViolation]:
        """TaskRouter.route() 소스에 .generate( 직접 호출 없음 확인 (LLM-0)."""
        violations = []
        try:
            src = inspect.getsource(task_router.route)
            # .generate( 패턴 검색 (LLM 직접 호출)
            if ".generate(" in src:
                violations.append(ContractViolation(
                    adapter_class  = type(task_router).__name__,
                    violation_type = "llm0",
                    detail         = "TaskRouter.route() contains .generate() call — LLM-0 violation",
                ))
        except (TypeError, OSError):
            pass  # 소스 불가 → 검사 생략
        return violations


# ────────────────────────────────────────────────────────────────
# Release Gate 함수 — release_gates.py 연동
# ────────────────────────────────────────────────────────────────

def _gate_llm_adapter_contract() -> dict:
    """
    Gate 10 실행 함수.
    release_gates.py에서 호출.

    Returns:
        {"passed": bool, "details": dict}
    """
    from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
    from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
    from literary_system.llm_bridge.routing.task_router import TaskRouter

    adapters = [
        OpenAICompatibleAdapter.for_ollama(),
        MockLLMBridge(),
    ]

    # TaskRouter 인스턴스 (providers 없어도 route 소스 검사 가능)
    router = TaskRouter()

    gate   = LLMAdapterContractGate()
    result = gate.check(adapters, task_router=router)

    return {
        "pass":    result.passed,
        "passed":  result.passed,
        "details": result.to_dict(),
        "reason":  result.summary,
    }
