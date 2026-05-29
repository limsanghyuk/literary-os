# CHANGELOG V628 — Grafana + Prometheus 모니터링 스택 (v10.33.0)

**날짜**: 2026-05-25  
**버전**: v10.33.0  
**이전**: V627 v10.32.0 / ServePlane Helm 신설 +50 TC

---

## 핵심 변경

### 신규 파일 (모니터링 — 3종)
- `deploy/monitoring/prometheus.yml` — 3개 scrape job (ServePlane/TrainPlane/Cost)
- `deploy/monitoring/grafana_dashboard.json` — 6개 패널 운영 대시보드
- `literary_system/ops/prometheus_exporter.py` (329 lines)
  - **PrometheusExporter**: 10종 메트릭 exposition format 출력
  - **MetricSnapshot**: 시점 스냅샷 dataclass (validate/is_healthy)
  - **MonitoringConfig**: 설정 dataclass (validate)

### 수정 파일
- `literary_system/ops/__init__.py` — 3종 export 추가
- `literary_system/gates/release_gate.py` — version "V628"
- `pyproject.toml` — 10.32.0 → 10.33.0
- `tools/test_inventory.json` — 7,090 TC

### 신규 TC (+30)
- `tests/unit/test_v628_monitoring.py` (267 lines)
  - TC-01~10: TestPrometheusExporterBasic
  - TC-11~20: TestMetricSnapshot
  - TC-21~30: TestGrafanaDashboardSpec

---

## Gate 상태
- **Gates**: 60/60 PASS
- **Tests**: 7,090 TC
- **G61 Phase B Exit**: 6/6 PASS
