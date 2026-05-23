# CHANGELOG — V578 (8.3.0)

**릴리즈 날짜**: 2026-05-19  
**버전**: 8.3.0  
**테스트**: 5,579 PASS / 35 Gates PASS  

---

## 주요 변경사항

### ADR-032: Gate Registry Single Source of Truth

릴리즈 게이트 메타데이터의 단일 정보 소스를 확립했습니다.

#### 신규 파일

| 파일 | 역할 |
|------|------|
| `literary_system/gates/gate_registry.py` | `GateRegistryEntry` + `GATE_REGISTRY` + 공개 API |
| `docs/adr/ADR-032.md` | Gate Registry 결정 기록 |
| `docs/adr/INDEX.md` | ADR 자동 추출 인덱스 (39개 ADR) |
| `tools/extract_adr.py` | ADR retroactive 자동 추출 스크립트 |
| `tests/test_v578_gate_registry.py` | V578 검증 테스트 25종 |
| `CHANGELOG_V578.md` | 본 파일 |

#### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `literary_system/gates/release_gate.py` | Gate G36 `_gate_registry_g36()` 추가 |
| `pyproject.toml` | 버전 8.2.0 → 8.3.0 |

---

## GATE_REGISTRY 구조

```python
from literary_system.gates.gate_registry import (
    GATE_REGISTRY,      # Dict[str, GateRegistryEntry] — 35개 게이트
    get_gate,           # gate_id → GateRegistryEntry | None
    list_gates,         # layer 필터 지원 ('L0'~'L4')
    run_all_gates,      # 전체 실행 → ADR/layer 메타데이터 포함 결과
    validate_registry,  # CI 검증 진입점
)
```

### GateRegistryEntry 5개 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `gate_id` | str | 게이트 고유 식별자 |
| `name` | str | 표시 이름 |
| `fn` | Callable | 실행 함수 |
| `adr_ref` | str | 관련 ADR (예: "ADR-035") |
| `version_added` | str | 추가 버전 (예: "V577") |
| `layer` | str | 계층 L0~L4 (ADR-028 기준) |

### L0 게이트 (핵심 불변 원칙)

- `llm_zero` (ADR-001) — LLM-0 외부 호출 금지
- `llm0_static_analysis` (ADR-031) — LLM-0 정적 분석
- `auth_regression_g34` (ADR-034) — DEV_MODE 보안 회귀 방지

---

## Gate G36 GateRegistry

레지스트리 자체의 무결성을 검증:
- GATE_REGISTRY ↔ GATES 1:1 매핑
- 모든 fn callable 확인
- layer L0~L4 유효성 확인

---

## tools/extract_adr.py

```bash
python tools/extract_adr.py
# → docs/adr/INDEX.md 생성 (39개 ADR 자동 추출)
```

git log + 소스 코드 grep으로 ADR-001~ADR-039 참조를 자동 발견합니다.

---

## 테스트 커버리지

| 그룹 | TC | 내용 |
|------|----|------|
| GateRegistryEntry | TC-01~05 | 불변 데이터클래스, run() |
| GateRegistryStructure | TC-06~10 | dict 구조, GATES 매핑 |
| PublicAPI | TC-11~13 | get_gate, list_gates |
| ValidateRegistry | TC-14~16 | CI 검증 |
| GateG36 | TC-17~19 | G36 존재, PASS, 등록 |
| RunAllGates | TC-20~22 | 통합 실행, 메타데이터 |
| ExtractADR | TC-23~25 | 스크립트, ADR-035 발견, INDEX.md |

**합계: 25 PASS**
