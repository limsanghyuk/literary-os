"""literary_system.causal_plan — 인과 계획 + 인과 연속 빌더."""
# V11.39.0 ADR-128: causal/ 패키지 통합
try:
    from literary_system.causal.causal_continuation_plan_builder import (
        CausalContinuationPlanBuilder,
        CausalPlan,
    )
except ImportError:
    CausalContinuationPlanBuilder = None
    CausalPlan = None
