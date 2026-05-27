"""V662 — ModelServingEndpointV2 테스트 (33 TC).

ADR-122: Kubernetes HPA 지원 서빙 엔드포인트 v2.0
"""
from __future__ import annotations

import time
import pytest

from literary_system.serving.model_serving_endpoint_v2 import (
    HPAConfig,
    HPAConfigError,
    HPAStatus,
    MetricsCollector,
    ServingMetricsSnapshot,
    ModelServingEndpointV2,
    generate_hpa_manifest,
)


# ── 헬퍼 ──────────────────────────────────────────────────────────────

def _snap(qps: float = 50.0, cpu: float = 60.0, mem: float = 50.0,
          queue: int = 0, replicas: int = 2) -> ServingMetricsSnapshot:
    return ServingMetricsSnapshot(
        timestamp=time.monotonic(),
        qps=qps,
        queue_depth=queue,
        cpu_utilization_pct=cpu,
        memory_utilization_pct=mem,
        active_replicas=replicas,
    )


def _cfg(**kw) -> HPAConfig:
    defaults = dict(min_replicas=2, max_replicas=10, target_cpu_utilization_pct=70,
                    target_memory_utilization_pct=80, target_rps=100.0,
                    scale_up_cooldown_sec=0, scale_down_cooldown_sec=0)
    defaults.update(kw)
    return HPAConfig(**defaults)


# ── TC-01~05: HPAConfig 유효성 검사 ─────────────────────────────────

class TestHPAConfig:
    def test_tc01_valid_config(self):
        """TC-01: 유효한 설정 — 예외 없음."""
        cfg = _cfg()
        cfg.validate()  # no raise

    def test_tc02_min_replicas_zero_raises(self):
        """TC-02: min_replicas=0 → HPAConfigError."""
        cfg = _cfg(min_replicas=0)
        with pytest.raises(HPAConfigError, match="min_replicas"):
            cfg.validate()

    def test_tc03_max_lt_min_raises(self):
        """TC-03: max_replicas < min_replicas → HPAConfigError."""
        cfg = _cfg(min_replicas=5, max_replicas=3)
        with pytest.raises(HPAConfigError, match="max_replicas"):
            cfg.validate()

    def test_tc04_cpu_pct_out_of_range(self):
        """TC-04: target_cpu_utilization_pct=0 → HPAConfigError."""
        cfg = _cfg(target_cpu_utilization_pct=0)
        with pytest.raises(HPAConfigError, match="target_cpu"):
            cfg.validate()

    def test_tc05_to_dict_has_keys(self):
        """TC-05: to_dict() 필수 키 포함."""
        d = _cfg().to_dict()
        for key in ("min_replicas", "max_replicas", "target_cpu_utilization_pct",
                    "target_rps", "namespace", "deployment_name"):
            assert key in d, f"missing: {key}"


# ── TC-06~09: MetricsCollector ────────────────────────────────────────

class TestMetricsCollector:
    def test_tc06_empty_returns_zero(self):
        """TC-06: 샘플 없으면 avg_qps=0."""
        col = MetricsCollector()
        assert col.avg_qps() == 0.0

    def test_tc07_avg_qps_computed(self):
        """TC-07: avg_qps 정상 계산."""
        col = MetricsCollector()
        col.record(_snap(qps=100.0))
        col.record(_snap(qps=200.0))
        assert col.avg_qps() == pytest.approx(150.0)

    def test_tc08_avg_cpu_computed(self):
        """TC-08: avg_cpu 정상 계산."""
        col = MetricsCollector()
        col.record(_snap(cpu=40.0))
        col.record(_snap(cpu=60.0))
        assert col.avg_cpu() == pytest.approx(50.0)

    def test_tc09_max_queue_depth(self):
        """TC-09: max_queue_depth 반환."""
        col = MetricsCollector()
        col.record(_snap(queue=3))
        col.record(_snap(queue=10))
        col.record(_snap(queue=5))
        assert col.max_queue_depth() == 10


# ── TC-10~14: HPAStatus ────────────────────────────────────────────────

class TestHPAStatus:
    def test_tc10_is_at_max(self):
        """TC-10: current==max → is_at_max=True."""
        st = HPAStatus(10, 10, 2, 10)
        assert st.is_at_max is True

    def test_tc11_is_at_min(self):
        """TC-11: current==min → is_at_min=True."""
        st = HPAStatus(2, 2, 2, 10)
        assert st.is_at_min is True

    def test_tc12_to_dict_keys(self):
        """TC-12: to_dict() 필수 키."""
        st = HPAStatus(3, 4, 2, 10, scale_direction="up")
        d = st.to_dict()
        for k in ("current_replicas", "desired_replicas", "scale_direction",
                   "is_at_max", "is_at_min", "conditions"):
            assert k in d

    def test_tc13_not_at_max_or_min(self):
        """TC-13: 중간 레플리카 수 — 둘 다 False."""
        st = HPAStatus(5, 5, 2, 10)
        assert st.is_at_max is False
        assert st.is_at_min is False

    def test_tc14_conditions_default_empty(self):
        """TC-14: conditions 기본값 빈 리스트."""
        st = HPAStatus(2, 2, 2, 10)
        assert st.conditions == []


# ── TC-15~22: ModelServingEndpointV2 핵심 ─────────────────────────────

class TestModelServingEndpointV2:
    def test_tc15_init_defaults(self):
        """TC-15: 기본 초기화 — 버전 2.0.0."""
        ep = ModelServingEndpointV2()
        assert ep.VERSION == "2.0.0"

    def test_tc16_liveness_probe_alive(self):
        """TC-16: 건강 상태 — liveness probe."""
        ep = ModelServingEndpointV2()
        result = ep.liveness_probe()
        assert result["status"] == "alive"
        assert "uptime_sec" in result

    def test_tc17_liveness_unhealthy(self):
        """TC-17: set_healthy(False) → liveness='unhealthy'."""
        ep = ModelServingEndpointV2()
        ep.set_healthy(False)
        assert ep.liveness_probe()["status"] == "unhealthy"

    def test_tc18_readiness_probe_ready(self):
        """TC-18: 기본 readiness probe — ready."""
        ep = ModelServingEndpointV2()
        result = ep.readiness_probe()
        assert result["status"] == "ready"

    def test_tc19_readiness_not_ready(self):
        """TC-19: set_ready(False) → readiness='not_ready'."""
        ep = ModelServingEndpointV2()
        ep.set_ready(False)
        assert ep.readiness_probe()["status"] == "not_ready"

    def test_tc20_status_dict_keys(self):
        """TC-20: status() 필수 키."""
        ep = ModelServingEndpointV2()
        st = ep.status()
        for k in ("version", "healthy", "ready", "current_replicas", "hpa", "metrics"):
            assert k in st

    def test_tc21_hpa_config_returned(self):
        """TC-21: hpa_config() → HPAConfig dict."""
        cfg = _cfg(min_replicas=3, max_replicas=15)
        ep = ModelServingEndpointV2(hpa_config=cfg)
        d = ep.hpa_config()
        assert d["min_replicas"] == 3
        assert d["max_replicas"] == 15

    def test_tc22_invalid_hpa_config_raises(self):
        """TC-22: 잘못된 HPAConfig → HPAConfigError."""
        bad = HPAConfig(min_replicas=0)
        with pytest.raises(HPAConfigError):
            ModelServingEndpointV2(hpa_config=bad)


# ── TC-23~28: 스케일 계산 ─────────────────────────────────────────────

class TestScaling:
    def test_tc23_compute_desired_no_metrics(self):
        """TC-23: 메트릭 없으면 현재 레플리카 유지."""
        ep = ModelServingEndpointV2(hpa_config=_cfg())
        assert ep.compute_desired_replicas() == ep._hpa.min_replicas

    def test_tc24_compute_scale_up_cpu(self):
        """TC-24: CPU 과부하 → 스케일업."""
        cfg = _cfg(min_replicas=2, max_replicas=10, target_cpu_utilization_pct=50)
        ep = ModelServingEndpointV2(hpa_config=cfg)
        ep.record_metrics(_snap(cpu=100.0))  # 2× 목표
        desired = ep.compute_desired_replicas()
        assert desired > ep._hpa.min_replicas

    def test_tc25_compute_clamped_to_max(self):
        """TC-25: 극단적 과부하 → max_replicas 클램프."""
        cfg = _cfg(min_replicas=2, max_replicas=5, target_cpu_utilization_pct=10)
        ep = ModelServingEndpointV2(hpa_config=cfg)
        ep.record_metrics(_snap(cpu=100.0))  # 10× 목표
        desired = ep.compute_desired_replicas()
        assert desired <= 5

    def test_tc26_force_scale_up(self):
        """TC-26: force_scale(8) → current_replicas=8."""
        ep = ModelServingEndpointV2(hpa_config=_cfg())
        st = ep.force_scale(8)
        assert st.current_replicas == 8
        assert st.scale_direction == "up"

    def test_tc27_force_scale_clamped(self):
        """TC-27: force_scale(999) → max_replicas."""
        ep = ModelServingEndpointV2(hpa_config=_cfg(max_replicas=10))
        st = ep.force_scale(999)
        assert st.current_replicas == 10

    def test_tc28_maybe_scale_returns_hpa_status(self):
        """TC-28: maybe_scale() → HPAStatus."""
        ep = ModelServingEndpointV2(hpa_config=_cfg())
        ep.record_metrics(_snap(cpu=70.0))
        result = ep.maybe_scale()
        assert isinstance(result, HPAStatus)


# ── TC-29~33: HPA YAML 생성 ──────────────────────────────────────────

class TestGenerateHPAManifest:
    def test_tc29_manifest_is_string(self):
        """TC-29: generate_hpa_manifest() → str."""
        cfg = _cfg()
        result = generate_hpa_manifest(cfg)
        assert isinstance(result, str)

    def test_tc30_manifest_has_hpa_kind(self):
        """TC-30: 매니페스트에 'HorizontalPodAutoscaler' 포함."""
        result = generate_hpa_manifest(_cfg())
        assert "HorizontalPodAutoscaler" in result

    def test_tc31_manifest_has_min_max(self):
        """TC-31: minReplicas / maxReplicas 반영."""
        cfg = _cfg(min_replicas=3, max_replicas=20)
        result = generate_hpa_manifest(cfg)
        assert "minReplicas: 3" in result
        assert "maxReplicas: 20" in result

    def test_tc32_manifest_has_cpu_target(self):
        """TC-32: CPU 목표 사용률 반영."""
        cfg = _cfg(target_cpu_utilization_pct=65)
        result = generate_hpa_manifest(cfg)
        assert "65" in result

    def test_tc33_manifest_invalid_config_raises(self):
        """TC-33: 잘못된 설정으로 manifest 생성 → HPAConfigError."""
        cfg = HPAConfig(min_replicas=0)
        with pytest.raises(HPAConfigError):
            generate_hpa_manifest(cfg)
