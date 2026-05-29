"""literary_system/ops — SP5 Production Operations 패키지."""

from literary_system.ops.analytics_dashboard import (
    AnalyticsDashboard,
    AnalyticsEvent,
    CohortReport,
    NPSResult,
    PublicAPIDoc,
)
from literary_system.ops.circuit_breaker_llm import (
    CircuitBreaker,
    CircuitBreakerEvent,
    CircuitBreakerOpenError,
    CircuitState,
)
from literary_system.ops.dr_controller import (
    DRController,
    DRStatus,
    DRTestResult,
    RestoreReport,
    Snapshot,
    WALEntry,
)
from literary_system.ops.load_balancer import (
    AdapterRef,
    LoadBalancer,
    RouteResult,
    weighted_round_robin,
)
from literary_system.ops.observability_stack import (
    LoadTestReport,
    LogEntry,
    LogLevel,
    Metric,
    ObservabilityStack,
    Span,
)
from literary_system.ops.production_launch_gate import (
    LaunchReport,
    ProductionLaunchGate,
    SLAAxis,
)
from literary_system.ops.helm_validator import (
    HelmValidator,
    HelmValidationResult,
    TrainPlaneChartSpec,
)
from literary_system.ops.user_onboarding import (
    OnboardResult,
    OnboardStep,
    PaymentGateway,
    Subscription,
    User,
    UserOnboarding,
    UserPlan,
    UserStatus,
)

__all__ = [
    "LoadBalancer", "AdapterRef", "RouteResult", "weighted_round_robin",
    "CircuitBreaker", "CircuitState", "CircuitBreakerOpenError", "CircuitBreakerEvent",
    "ObservabilityStack", "Span", "Metric", "LogEntry", "LoadTestReport", "LogLevel",
    "DRController", "Snapshot", "WALEntry", "RestoreReport", "DRStatus", "DRTestResult",
    "ProductionLaunchGate", "LaunchReport", "SLAAxis",
    "UserOnboarding", "User", "Subscription", "OnboardResult",
    "UserPlan", "UserStatus", "PaymentGateway", "OnboardStep",
    "AnalyticsDashboard", "PublicAPIDoc",
    "AnalyticsEvent", "CohortReport", "NPSResult",
    "HelmValidator", "HelmValidationResult", "TrainPlaneChartSpec",
]

from literary_system.ops.prometheus_exporter import (
    MetricSnapshot,
    MonitoringConfig,
    PrometheusExporter,
)

__all__ += [
    # prometheus_exporter (V628)
    "PrometheusExporter",
    "MetricSnapshot",
    "MonitoringConfig",
]

from literary_system.ops.ops_runbook import (
    OpsRunbook,
    RunbookStep,
    RunbookResult,
    StepResult,
    StepStatus,
    RunbookSeverity,
    build_health_check_runbook,
)

__all__ += [
    # ops_runbook (V629)
    "OpsRunbook",
    "RunbookStep",
    "RunbookResult",
    "StepResult",
    "StepStatus",
    "RunbookSeverity",
    "build_health_check_runbook",
]

# V11.39.0 ADR-128: optimization/ 운영 서브시스템 연결
try:
    from literary_system.optimization.adaptive_throttler import AdaptiveThrottler, ThrottleConfig
    from literary_system.optimization.long_run_monitor import LongRunMonitor, LongRunConfig
    from literary_system.optimization.memory_leak_detector import MemoryLeakDetector
    from literary_system.optimization.performance_optimizer import PerformanceOptimizer
except ImportError:
    AdaptiveThrottler = None
    LongRunMonitor = None
    MemoryLeakDetector = None
    PerformanceOptimizer = None

# V11.39.0 ADR-128: docs/ APIReferenceGenerator 연결
try:
    from literary_system.docs.api_reference_generator import (
        APIReferenceGenerator,
        APIReferenceReport,
    )
except ImportError:
    APIReferenceGenerator = None
    APIReferenceReport = None
