# CHANGELOG — V679

## 버전 정보
- 버전: 11.52.0
- 태그: v11.52.0 / v11.52.0-V679
- 날짜: 2026-05-27
- 서브페이즈: SP-C.4 안정화 5 — Enterprise 컴플라이언스 감사

## 변경 사항

### 신규 파일
- `literary_system/enterprise/compliance_audit.py` — G78 EnterpriseComplianceAuditGate
- `tests/unit/test_v679_compliance_audit.py` — 28 TC
- `docs/adr/ADR-141.md`
- `docs/changelog/CHANGELOG_V679.md`

### 수정 파일
- `literary_system/enterprise/__init__.py` — compliance_audit 모듈 export 추가
- `literary_system/gates/release_gate.py` — _gate_enterprise_compliance_audit_g78() (79 gates)
- `pyproject.toml` — version 11.52.0

## 주의
DuplicateZero G37 준수: AuditEventType→EnterpriseAuditEventType, AuditSeverity→EnterpriseAuditSeverity

## 테스트 결과
- test_v679_compliance_audit.py: 28/28 PASS
- Release Gate: 79/79 PASS
- Test Inventory: 8798 TC

## Gate
- G78 EnterpriseComplianceAuditGate: PASS (4 tenants, 1 non-compliant)
