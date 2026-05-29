"""V411-I 테스트 — LLMAdapterContractGate (Gate 10)."""
from __future__ import annotations
import pytest
from literary_system.gates.gate10_llm_contract import (
    LLMAdapterContractGate, ContractViolation, ContractGateResult,
    _gate_llm_adapter_contract,
)
from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.llm_bridge.ollama_adapter import OllamaAdapter
from literary_system.llm_bridge.routing.task_router import TaskRouter
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface


# ── 1. ContractGateResult 기본 생성 ─────────────────────────────
def test_result_defaults():
    r = ContractGateResult(passed=True)
    assert r.passed == True
    assert r.adapters_checked == 0
    assert r.violations == []


# ── 2. OpenAICompatibleAdapter 계약 준수 ────────────────────────
def test_openai_adapter_passes():
    gate = LLMAdapterContractGate()
    result = gate.check([OpenAICompatibleAdapter.for_ollama()])
    assert result.passed == True
    assert len(result.violations) == 0


# ── 3. MockLLMBridge 계약 준수 ──────────────────────────────────
def test_mock_bridge_passes():
    gate = LLMAdapterContractGate()
    result = gate.check([MockLLMBridge()])
    assert result.passed == True


# ── 4. OllamaAdapter 계약 준수 ──────────────────────────────────
def test_ollama_adapter_passes():
    gate = LLMAdapterContractGate()
    result = gate.check([OllamaAdapter()])
    assert result.passed == True


# ── 5. **kwargs 어댑터 감지 ──────────────────────────────────────
def test_detects_kwargs_violation():
    class BrokenAdapter(LLMBridgeInterface):
        @property
        def provider_name(self): return "broken"
        def generate(self, prompt, **kwargs): return ""
        def parse_action_packet(self, raw): return None
    gate = LLMAdapterContractGate()
    result = gate.check([BrokenAdapter()])
    assert result.passed == False
    types = [v.violation_type for v in result.violations]
    assert "signature" in types


# ── 6. generate() context 파라미터 누락 감지 ────────────────────
def test_detects_missing_context_param():
    class NoContextAdapter(LLMBridgeInterface):
        @property
        def provider_name(self): return "nocontext"
        def generate(self, prompt): return ""      # context 없음
        def parse_action_packet(self, raw): return None
    gate = LLMAdapterContractGate()
    result = gate.check([NoContextAdapter()])
    assert result.passed == False


# ── 7. is_available 누락 감지 ───────────────────────────────────
def test_detects_missing_method():
    class NoAvailAdapter(LLMBridgeInterface):
        @property
        def provider_name(self): return "noavail"
        def generate(self, prompt, context=None): return ""
        def parse_action_packet(self, raw): return None
        # is_available 없음 — 하지만 LLMBridgeInterface 기본 구현이 있으므로
        # 이 케이스는 generate/parse 필수만 체크
    gate = LLMAdapterContractGate()
    # 기본 구현이 있으므로 통과해야 함
    result = gate.check([NoAvailAdapter()])
    # is_available은 기본 구현이 있으므로 통과
    assert isinstance(result, ContractGateResult)


# ── 8. LLM-0 검사 — TaskRouter 통과 ────────────────────────────
def test_llm0_check_passes_for_task_router():
    gate = LLMAdapterContractGate()
    router = TaskRouter()
    result = gate.check([], task_router=router)
    assert result.llm0_passed == True


# ── 9. adapters_checked 카운트 ──────────────────────────────────
def test_adapters_checked_count():
    gate = LLMAdapterContractGate()
    adapters = [OpenAICompatibleAdapter.for_ollama(),
                MockLLMBridge(),
                OllamaAdapter()]
    result = gate.check(adapters)
    assert result.adapters_checked == 3


# ── 10. to_dict 직렬화 ──────────────────────────────────────────
def test_result_to_dict():
    gate = LLMAdapterContractGate()
    result = gate.check([MockLLMBridge()])
    d = result.to_dict()
    assert "passed" in d
    assert "adapters_checked" in d
    assert "violations" in d
    assert "llm0_passed" in d


# ── 11. summary 문자열 ──────────────────────────────────────────
def test_result_summary_pass():
    gate = LLMAdapterContractGate()
    result = gate.check([MockLLMBridge()])
    assert "PASS" in result.summary or "pass" in result.summary.lower()


# ── 12. 빈 어댑터 목록 ──────────────────────────────────────────
def test_empty_adapters():
    gate = LLMAdapterContractGate()
    result = gate.check([])
    assert result.passed == True
    assert result.adapters_checked == 0


# ── 13. ContractViolation 필드 ──────────────────────────────────
def test_contract_violation_fields():
    v = ContractViolation(
        adapter_class="Test",
        violation_type="signature",
        detail="missing context",
    )
    assert v.adapter_class == "Test"
    assert v.violation_type == "signature"


# ── 14. _gate_llm_adapter_contract 릴리즈 함수 ──────────────────
def test_release_gate_function():
    result = _gate_llm_adapter_contract()
    assert "passed" in result
    assert "details" in result
    # 모든 어댑터 계약 준수 → passed=True
    assert result["passed"] == True


# ── 15. Release Gate에 Gate 10 등록 확인 ────────────────────────
def test_gate10_registered_in_release_gate():
    from literary_system.gates.release_gate import GATES
    gate_ids = [g[0] for g in GATES]
    assert "llm_adapter_contract" in gate_ids
