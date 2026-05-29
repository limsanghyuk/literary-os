# CHANGELOG — V577 (8.2.0)

**릴리즈 날짜**: 2026-05-19  
**버전**: 8.2.0  
**테스트**: 5,554 PASS / 35 Gates PASS  

---

## 주요 변경사항

### ADR-035: LLM Adapter Canonical 단일화 (G3 우선)

4세대 어댑터 공존 문제를 해결하여 G3(`adapters_live/`)를 캐노니컬로 확립했습니다.

#### 신규 파일

| 파일 | 역할 |
|------|------|
| `literary_system/llm_bridge/canonical_adapter.py` | `CanonicalLLMBridge` + 팩토리 함수 3종 |
| `docs/adr/ADR-035.md` | LLM Adapter Canonical 결정 기록 |
| `tests/test_v577_adapter_canonical.py` | V577 검증 테스트 25종 |
| `CHANGELOG_V577.md` | 본 파일 |

#### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `literary_system/llm_bridge/gateway/unified_llm_gateway.py` | `make_default_gateway()` G1→G3 canonical 전환 |
| `literary_system/llm_bridge/claude_adapter.py` | V577 DEPRECATED 경고 추가 |
| `literary_system/llm_bridge/ollama_adapter.py` | V577 DEPRECATED 경고 추가 |
| `literary_system/llm_bridge/adapters_v2.py` | ClaudeAdapterV2/OllamaAdapterV2 DEPRECATED 경고 추가 |
| `literary_system/llm_bridge/adapters/anthropic_adapter.py` | V577 DEPRECATED 경고 추가 |
| `literary_system/llm_bridge/adapters/ollama_adapter.py` | V577 DEPRECATED 경고 추가 |
| `literary_system/gates/release_gate.py` | Gate G35 `_gate_adapter_canonical_g35()` 추가 |
| `pyproject.toml` | 버전 8.1.0 → 8.2.0 |

---

## CanonicalLLMBridge 설계

```
G3 어댑터 (adapters_live/)          LLMBridgeInterface 계약
  .call(ctx) → RealLLMResponse   ←→  .generate(prompt, ctx) → str
                                      CanonicalLLMBridge 래퍼
```

### 팩토리 함수

```python
from literary_system.llm_bridge.canonical_adapter import (
    make_canonical_claude,   # RealClaudeAdapter 기반
    make_canonical_ollama,   # RealOllamaAdapter 기반
    make_canonical_openai,   # RealOpenAIAdapter 기반
)

# LLM-0 원칙: call_fn 주입으로 CI 환경 보호
bridge = make_canonical_claude(
    model="claude-haiku-4-5-20251001",
    call_fn=mock_fn,
)
text = bridge.generate("프롬프트", ctx)
```

---

## Gate G35 AdapterCanonical

| 항목 | 검증 내용 |
|------|----------|
| IS-A 관계 | `CanonicalLLMBridge` → `LLMBridgeInterface` |
| generate() | mock call_fn 주입 후 정상 응답 반환 |
| provider_id | `claude/*` 포함 확인 |
| UnifiedLLMGateway | `make_default_gateway()` → `UnifiedLLMGateway` 반환 |
| G3 임포트 | `RealClaudeAdapter/RealOpenAIAdapter/RealOllamaAdapter` 3종 |

---

## G1/G2 Deprecation 경고 대상

V578 이후 제거 예정 (하위 호환 유지):

- `ClaudeAdapter` (G1_root: `llm_bridge/claude_adapter.py`)
- `OllamaAdapter` (G1_root: `llm_bridge/ollama_adapter.py`)
- `ClaudeAdapterV2`, `OllamaAdapterV2` (G2: `llm_bridge/adapters_v2.py`)
- `AnthropicAdapter` (G1_sub: `llm_bridge/adapters/anthropic_adapter.py`)
- `OllamaAdapter` (G1_sub: `llm_bridge/adapters/ollama_adapter.py`)

---

## 테스트 커버리지

| 그룹 | TC | 내용 |
|------|----|------|
| CanonicalLLMBridgeContract | TC-01~05 | IS-A, provider_name, provider_id |
| CanonicalFactoryFunctions | TC-06~09 | make_canonical_* 3종 |
| GenerateIntegration | TC-10~13 | generate() 흐름, LLM-0 mock |
| BridgeUtilityMethods | TC-14~16 | is_available(), cost_estimate() |
| UnifiedLLMGatewayG3 | TC-17~19 | G3 전환 검증 |
| GateG35 | TC-20~22 | G35 존재, PASS, 등록 |
| DeprecationWarnings | TC-23~25 | G1/G2 경고 코드 존재 |

**합계: 25 PASS**
