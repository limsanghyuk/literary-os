# CHANGELOG — V678

## 버전 정보
- 버전: 11.51.0
- 태그: v11.51.0 / v11.51.0-V678
- 날짜: 2026-05-27
- 서브페이즈: SP-C.4 안정화 4 — Enterprise 비용 제어

## 변경 사항

### 신규 파일
- `literary_system/enterprise/cost_control.py` — G77 EnterpriseCostControlGate
- `tests/unit/test_v678_cost_control.py` — 32 TC
- `docs/adr/ADR-140.md`
- `docs/changelog/CHANGELOG_V678.md`

### 수정 파일
- `literary_system/enterprise/__init__.py` — cost_control 모듈 export 추가
- `literary_system/gates/release_gate.py` — _gate_enterprise_cost_control_g77() (78 gates)
- `pyproject.toml` — version 11.51.0

## 테스트 결과
- test_v678_cost_control.py: 32/32 PASS
- Release Gate: 78/78 PASS
- Test Inventory: 8770 TC

## Gate
- G77 EnterpriseCostControlGate: PASS (4 tenants, 1 exceeded)
