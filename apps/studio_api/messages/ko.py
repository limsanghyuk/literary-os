"""
V428: i18n 메시지 — 한국어 (기본값)
ADR-001 준수: 표시 문자열은 이 파일에만 존재, 로직 코드에 하드코딩 금지.
"""
from __future__ import annotations

# ── Circuit Breaker 상태 메시지 ───────────────────────────────
CB_GATE_OPEN     = "게이트 Circuit OPEN -- 복구 대기 중"
CB_DRSE_OPEN     = "DRSE Circuit OPEN -- 분석 불가"
CB_NKG_OPEN      = "NKG Circuit OPEN -- 그래프 조회 불가"
CB_VOICE_OPEN    = "Voice Circuit OPEN -- 음성 분석 불가"
CB_GATE_DEGRADED = "게이트 실행 실패 -- 열화 모드"

# ── Remediation Hints ────────────────────────────────────────
HINT_OVERLOAD    = "클라이맥스 밀집 구간을 분산시키세요 (LoadBalancer 조정)"
HINT_VOICE_DRIFT = "캐릭터 음성 일관성을 확인하세요 (VoiceManifold 재검토)"
HINT_PAYOFF_DEBT = "미지불 Payoff Debt를 해소하세요 (PayoffDebt 체크)"
HINT_FATIGUE     = "독자 주의력 피로 구간을 조정하세요 (AttentionEconomy 최적화)"

# ── ManuscriptImporter 경고 ──────────────────────────────────
WARN_NO_DELIMITER = "씬 구분자를 찾을 수 없어 분리 실패"

# ── 일반 상태 ────────────────────────────────────────────────
DEGRADED_MODE    = "열화 모드"
GATE_EXEC_FAILED = "게이트 실행 실패"
CIRCUIT_BREAKER  = "Circuit Breaker"
RECOVERY_WAITING = "복구 대기 중"
