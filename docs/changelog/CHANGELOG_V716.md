# CHANGELOG V716

**버전**: 12.3.0  
**날짜**: 2026-05-28  
**커밋 메시지**: V716 SP-D.3: Plugin Registry Gate G87 구현 (ADR-177, 33 TC)

---

## 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/gates/plugin_registry_gate.py` | G87 게이트 7 체크포인트 (PR-1~PR-7) |
| `tests/unit/test_v716_plugin_registry_gate.py` | 33 TC (TC01~TC33) |
| `docs/adr/ADR-177.md` | Plugin Registry Gate 설계 결정 |

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `literary_system/gates/release_gate.py` | G87 `_gate_plugin_registry_g87()` 추가 |
| `pyproject.toml` | version 12.2.0 → 12.3.0 |

## Gate 결과

- **G87**: 7/7 체크포인트 PASS (PR-1~PR-7)
- **누적 GATES**: 84개
- **ADR-128 고립 해소**: plugins 패키지 V714~V715 2회 연속 고립 → V716 연결 완료

## 테스트

| 항목 | 수치 |
|------|------|
| 신규 TC | 33 |
| V716 이전 누적 | 9,865 |
| V716 총 누적 | 9,898 |
