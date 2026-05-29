# CHANGELOG — V626 (2026-05-25)

## Literary OS v10.31.0

### 신규
- `literary_system/ops/helm_validator.py`: HelmValidator (539 lines)
  - 9개 체크포인트: chart_dir / Chart.yaml / values.yaml / namespace / GPU / costSlo / LoRA / templates / SA
  - TrainPlaneChartSpec: 기대 스펙 상수 집합
  - HelmValidationResult: 검증 결과 데이터 클래스
  - _minimal_yaml_parse(): PyYAML 없는 환경 폴백
- `tests/unit/test_v626_helm_validator.py`: +30 TC (30/30 PASS)
- `docs/adr/ADR-093.md`: TrainPlane Helm 검증 전략
- `literary_system/ops/__init__.py`: HelmValidator 3종 export 추가

### 수정
- `literary_system/gates/release_gate.py`: version "V625" → "V626"
- `pyproject.toml`: 10.30.0 → 10.31.0
- `tools/test_inventory.json`: 7,010 TC

### 지표
- Gates: 60/60 PASS
- Tests: 7,010 (+30 TC)
- Version: v10.31.0
- G61 Phase B Exit: 6/6 PASS
