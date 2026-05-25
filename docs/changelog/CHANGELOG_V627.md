# CHANGELOG V627 — ServePlane Helm 신설 + 검증 (v10.32.0)

**날짜**: 2026-05-25  
**버전**: v10.32.0  
**커밋**: (pending)  
**이전**: V626 v10.31.0 / HelmValidator +30 TC

---

## 핵심 변경

### 신규 파일 (Helm chart — 4종)

- `deploy/helm/serve_plane/Chart.yaml` — apiVersion=v2, literary-os-serve-plane
- `deploy/helm/serve_plane/values.yaml` — literary-serve 네임스페이스, CPU 전용, LLM-1
- `deploy/helm/serve_plane/templates/deployment.yaml` — CPU 추론 Deployment
- `deploy/helm/serve_plane/templates/service.yaml` — ClusterIP Service
- `deploy/helm/serve_plane/templates/hpa.yaml` — HPA (CPU/Memory)

### 신규 파일 (Validator — 1종)

- `literary_system/serving/serve_plane_validator.py` (630 lines)
  - **ServePlaneValidator**: 11체크포인트 정적 검증기
  - **ServePlaneValidationResult**: 결과 dataclass
  - **ServePlaneChartSpec**: 기대 스펙 상수 dataclass
  - **ServePlaneValuesSpec**: values 기대값 dataclass

### 수정 파일

- `literary_system/serving/__init__.py` — 4종 export 추가
- `literary_system/gates/release_gate.py` — version "V627"
- `pyproject.toml` — 10.31.0 → 10.32.0
- `tools/test_inventory.json` — 7,060 TC

### 신규 TC (+50)

- `tests/unit/test_v627_serve_plane_helm.py` (487 lines)
  - TC-01~10: TestServePlaneValidatorBasic
  - TC-11~20: TestServePlaneValidatorMethods
  - TC-21~30: TestLLM1AndNamespaceIsolation
  - TC-31~40: TestCPUResourcesAndHPA
  - TC-41~50: TestEdgeCasesAndIntegration

### 문서

- `docs/adr/ADR-094.md` — ServePlane Helm 검증 전략
- `docs/changelog/CHANGELOG_V627.md` (이 파일)
- `manifests/MANIFEST_V627.md`

---

## Gate 상태

- **Gates**: 60/60 PASS (V627)
- **Tests**: 7,060 TC
- **G61 Phase B Exit**: 6/6 체크포인트 PASS

---

## ADR 연계

| ADR | 내용 |
|-----|------|
| ADR-057 §5 | TrainPlane/ServePlane 네임스페이스 격리 |
| ADR-058 | LLM-1 — PROMOTED 단계 모델만 서빙 |
| ADR-093 | TrainPlane Helm 검증 (V626) |
| ADR-094 | ServePlane Helm 검증 (V627, 이번) |
