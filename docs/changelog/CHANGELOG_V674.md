# CHANGELOG V674 — RevenueGate G74 (SP-C.4)

**버전**: 11.47.0  
**날짜**: 2026-05-27  
**단계**: SP-C.4 Competitive Absorption — Enterprise Layer

## 변경 요약

### 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/enterprise/revenue.py` | RevenueModel/Contract/Calculator/Generator/Gate (G74) |
| `tests/unit/test_v674_revenue_gate.py` | G74 단위 테스트 30 TC |
| `docs/adr/ADR-136.md` | Revenue Share 설계 결정 기록 |

### 수정 파일

| 파일 | 변경 |
|------|------|
| `literary_system/enterprise/__init__.py` | RevenueGate 등 9개 심볼 추가 |
| `literary_system/gates/release_gate.py` | `_gate_revenue_g74()` 추가 (Gate 75번째) |

## 기술 세부사항

### RevenueModel (3종)
- FLAT: 고정 요율 (예: 20%)
- TIERED: 구간 오름차순 요율 (예: 0~1K: 25%, 1K+: 15%)
- USAGE_BASED: 단위당 요율 (예: $0.05/unit)

### 인보이스 정합성 보장
- `partner_share + platform_share == gross_revenue` (오차 < 0.01)
- 음수 매출 거부, 고아 인보이스(계약 없음) 거부

## 게이트 결과

- **G74 (RevenueGate)**: PASS (3/3 인보이스 통과)
- **전체 Release Gate**: 75/75 PASS ✅
- **단위 테스트**: 30/30 PASS ✅
- **총 TC**: 8,658

## 다음 단계

V675: SP-C.4 안정화 — 통합 테스트 강화
