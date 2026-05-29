# Changelog: V741 ~ V743 (G91 Disaster Recovery Gate)

**릴리즈 버전**: v12.5.10  
**날짜**: 2026-05-29  
**Phase**: SP-D.4 (Phase D Sub-phase 4)  
**태그**: `v12.5.10`, `v12.5.10-V741-V743`  

---

## 개요

D-M-11 요구사항 구현: G91 Disaster Recovery Gate 신설.
RPO ≤ 1h 정책을 코드 레벨에서 강제하는 `DRBackupManager` / `DRRestoreManager` 구현 및
5개 체크(DR-1~DR-5)를 포함하는 G91 Gate를 GATES에 등록한다.

---

## V741 — DRBackupManager (D-M-11 Phase 1)

### 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/disaster_recovery/__init__.py` | disaster_recovery 서브패키지 초기화 |
| `literary_system/disaster_recovery/backup_manager.py` | DRBackupManager (RPO 강제, SHA-256 체크섬, 프루닝) |

### 핵심 불변식

```python
DRBackupManager(backup_interval_seconds=3601)  # → ValueError
DRBackupManager(backup_interval_seconds=3600)  # → OK
```

---

## V742 — DRRestoreManager + DR Gate 체크 (D-M-11 Phase 2)

### 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/disaster_recovery/restore_manager.py` | DRRestoreManager (체크섬 검증, RTO 추적) |
| `literary_system/gates/dr_gate.py` | DR-1~DR-5 체크함수 + run_dr_gate() |

### DR 체크 5종

| ID | 검증 |
|----|------|
| DR-1 | RPO enforcement (3601s → ValueError) |
| DR-2 | 백업 생성 + SHA-256 |
| DR-3 | RPO compliance 윈도우 (3600s 경계) |
| DR-4 | 복원 + 체크섬 검증 (변조 감지) |
| DR-5 | E2E (백업→프루닝→테넌트격리→복원) |

---

## V743 — G91 Gate 등록 + ADR-202~204 + 테스트

### 신규/수정 파일

| 파일 | 설명 |
|------|------|
| `literary_system/gates/release_gate.py` | G91 dr_g91 GATES 등록 (총 93개) |
| `tests/unit/test_v741_v743_dr_gate.py` | 40 TC (TC01~TC40) |
| `docs/adr/ADR-202.md` | DRBackupManager 전략 |
| `docs/adr/ADR-203.md` | G91 DR Gate 설계 |
| `docs/adr/ADR-204.md` | RPO/RTO 정책 |

### Gate 통계

| 항목 | 값 |
|------|-----|
| GATES 총수 | 93개 (G91 추가) |
| G91 결과 | 5/5 DR checks PASS, approved=True |

### 테스트 결과

- **V741~V743 신규**: 40/40 PASS
- **전체 스위트**: 4,192 PASS (기존 26 failures pre-existing)

---

## 통계 요약

| 항목 | V740 기준 | V743 기준 | 증가 |
|------|-----------|-----------|------|
| PyPI version | 12.5.8 | 12.5.10 | +2 |
| 단위 테스트 PASS | 4,152 | 4,192 | +40 |
| ADR 문서 | ADR-201 | ADR-204 | +3 |
| GATES | 92 | 93 | +1 (G91) |
