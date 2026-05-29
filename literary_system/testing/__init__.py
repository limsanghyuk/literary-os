"""
literary_system.testing — V624 장기 시나리오 + 메모리 회귀 검증 모듈.

V624 (ADR-091):
  - LongRunScenario: 24h 압축 시뮬레이션 실행
  - MemoryRegressionChecker: 연속 실행간 메모리 회귀 감지
"""
from .long_run_scenario import LongRunScenario, LongRunSnapshot, LongRunScenarioReport
from .memory_regression import MemoryRegressionChecker, MemRegSnapshot, RegressionResult

__all__ = [
    "LongRunScenario",
    "LongRunSnapshot",
    "LongRunScenarioReport",
    "MemoryRegressionChecker",
    "MemRegSnapshot",
    "RegressionResult",
]
