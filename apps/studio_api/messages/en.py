"""
V428: i18n 메시지 — English
"""
from __future__ import annotations

# ── Circuit Breaker status messages ──────────────────────────
CB_GATE_OPEN     = "Gate Circuit OPEN -- awaiting recovery"
CB_DRSE_OPEN     = "DRSE Circuit OPEN -- analysis unavailable"
CB_NKG_OPEN      = "NKG Circuit OPEN -- graph query unavailable"
CB_VOICE_OPEN    = "Voice Circuit OPEN -- voice analysis unavailable"
CB_GATE_DEGRADED = "Gate execution failed -- degraded mode"

# ── Remediation Hints ────────────────────────────────────────
HINT_OVERLOAD    = "Spread out climax-dense segments (adjust LoadBalancer)"
HINT_VOICE_DRIFT = "Check character voice consistency (review VoiceManifold)"
HINT_PAYOFF_DEBT = "Resolve unpaid Payoff Debt (check PayoffDebt)"
HINT_FATIGUE     = "Adjust reader attention fatigue zones (optimize AttentionEconomy)"

# ── ManuscriptImporter warnings ──────────────────────────────
WARN_NO_DELIMITER = "No scene delimiter found — split failed"

# ── General status ───────────────────────────────────────────
DEGRADED_MODE    = "degraded mode"
GATE_EXEC_FAILED = "gate execution failed"
CIRCUIT_BREAKER  = "Circuit Breaker"
RECOVERY_WAITING = "awaiting recovery"
