"""
test_v624_long_run_scenario.py — V624 LongRunScenario + MemoryRegressionChecker
테스트 스위트 (ADR-091, 30 TC)

TC-01 ~ TC-10: LongRunScenario 단위 테스트
TC-11 ~ TC-20: MemoryRegressionChecker 단위 테스트
TC-21 ~ TC-30: 통합 + 크로스 컴포넌트 테스트
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ─────────────────────────────────────────────────────────────────────────────
# TC-01 ~ TC-10: LongRunScenario
# ─────────────────────────────────────────────────────────────────────────────

class TestLongRunScenario:
    """TC-01~10: LongRunScenario 단위 검증"""

    def test_01_import(self):
        """TC-01: LongRunScenario 임포트 + VERSION 확인"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        assert LongRunScenario.VERSION == "1.0.0"

    def test_02_run_3_epoch(self):
        """TC-02: 3 epoch 압축 실행 — 예외 없이 완료"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        lr = LongRunScenario(epoch_count=3)
        report = lr.run()
        assert report.epoch_count == 3

    def test_03_report_all_pass(self):
        """TC-03: 3 epoch 실행 후 all_pass == True"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        report = LongRunScenario(epoch_count=3).run()
        assert report.all_pass is True, f"FAIL: {report.summary()}"

    def test_04_memory_growth_within_limit(self):
        """TC-04: 메모리 증가량이 MAX(50MB) 이내"""
        from literary_system.testing.long_run_scenario import LongRunScenario, MAX_MEMORY_GROWTH_MB
        report = LongRunScenario(epoch_count=3).run()
        assert report.memory_growth_mb < MAX_MEMORY_GROWTH_MB

    def test_05_snapshot_count(self):
        """TC-05: 스냅샷 수 = epoch_count"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        lr = LongRunScenario(epoch_count=5)
        report = lr.run()
        assert len(report.snapshots) == 5

    def test_06_snapshot_fields(self):
        """TC-06: 스냅샷에 필수 필드 포함"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        snap = report.snapshots[0]
        assert snap.epoch == 1
        assert snap.elapsed_ms >= 0
        assert snap.memory_mb >= 0

    def test_07_component_results_in_snapshot(self):
        """TC-07: 스냅샷 component_results 5종 이상"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        snap = report.snapshots[0]
        assert len(snap.component_results) >= 5

    def test_08_is_stable_after_run(self):
        """TC-08: 정상 실행 후 is_stable() == True"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        lr = LongRunScenario(epoch_count=3)
        lr.run()
        assert lr.is_stable()

    def test_09_custom_hook(self):
        """TC-09: custom_hook 추가 — 결과에 반영"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        hook_called = []
        def my_hook(epoch: int) -> bool:
            hook_called.append(epoch)
            return True
        lr = LongRunScenario(epoch_count=2, custom_hooks={"test_hook": my_hook})
        report = lr.run()
        assert len(hook_called) == 2
        assert "hook:test_hook" in report.snapshots[0].component_results

    def test_10_report_to_dict(self):
        """TC-10: LongRunScenarioReport.to_dict() 필수 키 포함"""
        from literary_system.testing.long_run_scenario import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        d = report.to_dict()
        for key in ("all_pass", "epoch_count", "memory_growth_mb", "peak_memory_mb", "summary"):
            assert key in d, f"to_dict() 키 누락: {key}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-11 ~ TC-20: MemoryRegressionChecker
# ─────────────────────────────────────────────────────────────────────────────

class TestMemoryRegressionChecker:
    """TC-11~20: MemoryRegressionChecker 단위 검증"""

    def test_11_import(self):
        """TC-11: MemoryRegressionChecker 임포트 + VERSION"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        assert MemoryRegressionChecker.VERSION == "1.0.0"

    def test_12_check_5_runs(self):
        """TC-12: 5 run 실행 — 예외 없이 완료"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        mc = MemoryRegressionChecker(run_count=5)
        result = mc.check()
        assert result.run_count == 5

    def test_13_result_passed(self):
        """TC-13: 5 run 정상 실행 후 passed == True"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        result = MemoryRegressionChecker(run_count=5).check()
        assert result.passed is True, f"FAIL: {result.summary()}"

    def test_14_snapshot_count(self):
        """TC-14: 스냅샷 수 == run_count"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        result = MemoryRegressionChecker(run_count=4).check()
        assert len(result.snapshots) == 4

    def test_15_slope_within_limit(self):
        """TC-15: 기울기 < REGRESSION_SLOPE_MB_PER_RUN"""
        from literary_system.testing.memory_regression import (
            MemoryRegressionChecker, REGRESSION_SLOPE_MB_PER_RUN
        )
        result = MemoryRegressionChecker(run_count=5).check()
        assert result.slope_mb_per_run < REGRESSION_SLOPE_MB_PER_RUN

    def test_16_total_growth_within_limit(self):
        """TC-16: 총 메모리 증가 < MAX_TOTAL_GROWTH_MB"""
        from literary_system.testing.memory_regression import (
            MemoryRegressionChecker, MAX_TOTAL_GROWTH_MB
        )
        result = MemoryRegressionChecker(run_count=5).check()
        assert result.total_growth_mb < MAX_TOTAL_GROWTH_MB

    def test_17_is_stable_after_check(self):
        """TC-17: 정상 실행 후 is_stable() == True"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        mc = MemoryRegressionChecker(run_count=5)
        mc.check()
        assert mc.is_stable()

    def test_18_custom_workload(self):
        """TC-18: 커스텀 workload 적용"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        called = []
        def my_workload(i: int) -> None:
            called.append(i)
        mc = MemoryRegressionChecker(run_count=3, workload=my_workload)
        mc.check()
        assert len(called) == 3

    def test_19_linear_slope_zero_constant(self):
        """TC-19: 상수 데이터 기울기 == 0"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        checker = MemoryRegressionChecker.__new__(MemoryRegressionChecker)
        slope = checker._linear_slope([5.0, 5.0, 5.0, 5.0, 5.0])
        assert abs(slope) < 1e-9

    def test_20_result_to_dict(self):
        """TC-20: RegressionResult.to_dict() 필수 키 포함"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        result = MemoryRegressionChecker(run_count=3).check()
        d = result.to_dict()
        for key in ("run_count", "slope_mb_per_run", "total_growth_mb", "passed", "summary"):
            assert key in d, f"to_dict() 키 누락: {key}"


# ─────────────────────────────────────────────────────────────────────────────
# TC-21 ~ TC-30: 통합 + 크로스 컴포넌트
# ─────────────────────────────────────────────────────────────────────────────

class TestV624CrossIntegration:
    """TC-21~30: V624 통합 + 크로스 컴포넌트 검증"""

    def test_21_testing_package_init_import(self):
        """TC-21: literary_system.testing 패키지 임포트"""
        from literary_system.testing import (
            LongRunScenario, LongRunScenarioReport, LongRunSnapshot,
            MemoryRegressionChecker, MemRegSnapshot, RegressionResult,
        )
        assert True

    def test_22_longrun_and_regression_sequential(self):
        """TC-22: LongRunScenario → MemoryRegressionChecker 순차 실행"""
        from literary_system.testing import LongRunScenario, MemoryRegressionChecker
        lr_report = LongRunScenario(epoch_count=3).run()
        mr_result = MemoryRegressionChecker(run_count=3).check()
        assert lr_report.all_pass
        assert mr_result.passed

    def test_23_longrun_no_failed_epochs(self):
        """TC-23: LongRunScenario 실패 epoch 0건"""
        from literary_system.testing import LongRunScenario
        report = LongRunScenario(epoch_count=4).run()
        assert report.failed_epochs == []

    def test_24_memory_regression_no_errors(self):
        """TC-24: MemoryRegressionChecker 에러 0건"""
        from literary_system.testing import MemoryRegressionChecker
        result = MemoryRegressionChecker(run_count=4).check()
        assert result.errors == []

    def test_25_longrun_with_cim_v2_and_agent(self):
        """TC-25: LongRunScenario 내 CIMv2 + AgentRoutingPolicy 컴포넌트 PASS"""
        from literary_system.testing import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        for snap in report.snapshots:
            assert snap.component_results.get("cim_v2_cycle") is True
            assert snap.component_results.get("agent_routing") is True

    def test_26_regression_checker_slope_direction(self):
        """TC-26: 지속 증가 데이터 → 양수 기울기 감지"""
        from literary_system.testing.memory_regression import MemoryRegressionChecker
        checker = MemoryRegressionChecker.__new__(MemoryRegressionChecker)
        slope = checker._linear_slope([1.0, 2.0, 3.0, 4.0, 5.0])
        assert slope > 0

    def test_27_longrun_summary_contains_pass(self):
        """TC-27: LongRunScenarioReport.summary() 'PASS' 포함"""
        from literary_system.testing import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        assert "PASS" in report.summary()

    def test_28_regression_summary_contains_pass(self):
        """TC-28: RegressionResult.summary() 'PASS' 포함"""
        from literary_system.testing import MemoryRegressionChecker
        result = MemoryRegressionChecker(run_count=3).check()
        assert "PASS" in result.summary()

    def test_29_longrun_with_shared_char_and_reward(self):
        """TC-29: LongRunScenario 내 SharedChar + RewardModel 컴포넌트 PASS"""
        from literary_system.testing import LongRunScenario
        report = LongRunScenario(epoch_count=2).run()
        for snap in report.snapshots:
            assert snap.component_results.get("shared_char_cycle") is True
            assert snap.component_results.get("reward_model_cycle") is True

    def test_30_v624_module_constants(self):
        """TC-30: 모듈 상수 값 검증"""
        from literary_system.testing.long_run_scenario import (
            EPOCH_COUNT, MAX_MEMORY_GROWTH_MB, MAX_EPOCH_LATENCY_MS
        )
        from literary_system.testing.memory_regression import (
            DEFAULT_RUN_COUNT, REGRESSION_SLOPE_MB_PER_RUN, MAX_TOTAL_GROWTH_MB
        )
        assert EPOCH_COUNT == 24
        assert MAX_MEMORY_GROWTH_MB == 50.0
        assert MAX_EPOCH_LATENCY_MS == 2000.0
        assert DEFAULT_RUN_COUNT == 10
        assert REGRESSION_SLOPE_MB_PER_RUN == 5.0
        assert MAX_TOTAL_GROWTH_MB == 30.0
