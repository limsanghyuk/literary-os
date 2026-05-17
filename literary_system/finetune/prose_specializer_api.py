"""
ProseSpecializerAPI — 파인튜닝 모델 서빙 API (V473)

ADR-010: Graceful Degradation Tiers
ADR-017: Canary Deployment

설계:
  - 파인튜닝 모델 우선 서빙 (카나리 트래픽 기반)
  - 폴백 체인: FineTuned → Base → Mock
  - A/B 비교 지원
  - LLM-0: 라우팅·폴백 로직 규칙 기반 (실제 모델 호출 아님)
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class ServingTier(str, Enum):
    FINETUNED = "finetuned"   # 파인튜닝 모델 (1순위)
    BASE = "base"             # 베이스 모델 (폴백)
    MOCK = "mock"             # 목 응답 (최후 폴백)


class ABGroup(str, Enum):
    CONTROL = "control"       # 베이스 모델
    TREATMENT = "treatment"   # 파인튜닝 모델


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class ServeRequest:
    request_id: str
    prompt: str
    style_hint: str = ""
    tenant_id: str = ""
    ab_group: ABGroup | None = None
    max_tokens: int = 512
    temperature: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "style_hint": self.style_hint,
            "tenant_id": self.tenant_id,
            "ab_group": self.ab_group.value if self.ab_group else None,
        }


@dataclass
class ServeResponse:
    request_id: str
    generated_text: str
    serving_tier: ServingTier
    model_version_id: str | None
    ab_group: ABGroup | None
    latency_ms: float
    token_count: int
    served_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "generated_text": self.generated_text,
            "serving_tier": self.serving_tier.value,
            "model_version_id": self.model_version_id,
            "ab_group": self.ab_group.value if self.ab_group else None,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "served_at": self.served_at,
        }


@dataclass
class ABComparisonResult:
    comparison_id: str
    prompt: str
    control_response: ServeResponse
    treatment_response: ServeResponse
    winner: ABGroup | None
    metrics: dict[str, Any]
    compared_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "winner": self.winner.value if self.winner else None,
            "metrics": self.metrics,
            "compared_at": self.compared_at,
        }


# ---------------------------------------------------------------------------
# 목 생성기 (LLM-0 — 실제 모델 호출 없음)
# ---------------------------------------------------------------------------

def _mock_generate(prompt: str, style_hint: str, max_tokens: int) -> str:
    """
    LLM-0 목 생성기. 실제 서비스에서는 실 모델로 교체.
    스타일 힌트 기반 고정 패턴 반환.
    """
    style_templates: dict[str, str] = {
        "romance": "그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못한 채, 그녀는 미소를 지었다.",
        "thriller": "발소리가 점점 가까워졌다. 그는 숨을 죽이며 어둠 속에 몸을 숨겼다.",
        "sf": "우주선의 엔진이 윙윙거리며 작동했다. 인공지능 시스템이 목적지 좌표를 계산했다.",
        "historical": "조선의 하늘 아래, 장군은 칼을 빼들었다. 전쟁의 북소리가 멀리서 울려 퍼졌다.",
        "contemporary": "스마트폰 알림이 울렸다. 그는 카페에서 커피를 홀짝이며 메시지를 확인했다.",
    }
    base = style_templates.get(style_hint, f"[{style_hint}] " + prompt[:50] + "...")
    # 토큰 수 맞춤 (간단)
    words = base.split()
    target_words = min(max_tokens // 4, len(words))
    return " ".join(words[:max(1, target_words)])


# ---------------------------------------------------------------------------
# ProseSpecializerAPI
# ---------------------------------------------------------------------------

class ProseSpecializerAPI:
    """
    ADR-010/017 파인튜닝 모델 서빙 API.

    serve(request) → ServeResponse
      - 카나리 트래픽 비율에 따라 파인튜닝 모델 or 베이스 모델 선택
      - 폴백 체인: FINETUNED → BASE → MOCK

    compare_ab(prompt, style_hint) → ABComparisonResult
      - 컨트롤(베이스) vs 트리트먼트(파인튜닝) 동시 실행

    LLM-0: 라우팅·폴백 규칙 기반. 생성 로직은 mock.
    """

    def __init__(
        self,
        active_version_id: str | None = None,
        canary_pct: int = 0,
    ) -> None:
        self._active_version_id = active_version_id
        self._canary_pct = canary_pct       # 0~100
        self._responses: list[ServeResponse] = []
        self._ab_results: list[ABComparisonResult] = []

    def set_active_version(self, version_id: str, canary_pct: int) -> None:
        """활성 파인튜닝 모델 버전 설정"""
        self._active_version_id = version_id
        self._canary_pct = max(0, min(100, canary_pct))

    # ------------------------------------------------------------------
    # 서빙
    # ------------------------------------------------------------------

    def serve(self, request: ServeRequest) -> ServeResponse:
        """
        요청 라우팅:
        - A/B 그룹 지정 시 해당 그룹으로 고정
        - 미지정 시 canary_pct 기반 확률 라우팅
        """
        import time
        t0 = time.time()

        tier, version_id, ab_group = self._route(request)
        generated = _mock_generate(request.prompt, request.style_hint, request.max_tokens)
        latency_ms = round((time.time() - t0) * 1000, 2)

        resp = ServeResponse(
            request_id=request.request_id,
            generated_text=generated,
            serving_tier=tier,
            model_version_id=version_id,
            ab_group=ab_group,
            latency_ms=latency_ms,
            token_count=len(generated.split()),
            served_at=datetime.now(timezone.utc).isoformat(),
        )
        self._responses.append(resp)
        return resp

    def _route(
        self, request: ServeRequest
    ) -> tuple[ServingTier, str | None, ABGroup | None]:
        """
        라우팅 결정:
        1. A/B 그룹 명시: CONTROL→BASE, TREATMENT→FINETUNED
        2. 카나리 트래픽: request_id 해시로 결정론적 라우팅
        3. 활성 버전 없음: BASE 폴백
        """
        ab_group: ABGroup | None = request.ab_group

        if self._active_version_id is None or self._canary_pct == 0:
            # 파인튜닝 모델 없음 → BASE
            return ServingTier.BASE, None, ab_group

        if ab_group == ABGroup.CONTROL:
            return ServingTier.BASE, None, ab_group
        if ab_group == ABGroup.TREATMENT:
            return ServingTier.FINETUNED, self._active_version_id, ab_group

        # 결정론적 해시 라우팅 (같은 request_id → 같은 결과)
        h = int(hashlib.md5(request.request_id.encode()).hexdigest(), 16)
        bucket = h % 100  # 0~99
        if bucket < self._canary_pct:
            return ServingTier.FINETUNED, self._active_version_id, None
        return ServingTier.BASE, None, None

    # ------------------------------------------------------------------
    # A/B 비교
    # ------------------------------------------------------------------

    def compare_ab(
        self,
        prompt: str,
        style_hint: str = "",
        tenant_id: str = "",
    ) -> ABComparisonResult:
        """컨트롤(베이스) vs 트리트먼트(파인튜닝) 동시 실행"""
        req_id_base = str(uuid.uuid4())
        req_id_ft = str(uuid.uuid4())

        control_req = ServeRequest(
            request_id=req_id_base,
            prompt=prompt,
            style_hint=style_hint,
            tenant_id=tenant_id,
            ab_group=ABGroup.CONTROL,
        )
        treatment_req = ServeRequest(
            request_id=req_id_ft,
            prompt=prompt,
            style_hint=style_hint,
            tenant_id=tenant_id,
            ab_group=ABGroup.TREATMENT,
        )

        control_resp = self.serve(control_req)
        treatment_resp = self.serve(treatment_req)

        # 간단한 승자 결정: 토큰 수가 많고 스타일 키워드 더 많은 쪽
        def style_score(text: str, hint: str) -> float:
            keywords = {
                "romance": ['사랑', '설레', '마음', '눈빛'],
                "thriller": ['공포', '어둠', '숨', '발소리'],
                "sf": ['우주', '엔진', '시스템', '인공지능'],
                "historical": ['조선', '장군', '칼', '전쟁'],
                "contemporary": ['스마트폰', '카페', '메시지', '커피'],
            }
            kws = keywords.get(hint, [])
            return sum(1 for kw in kws if kw in text) / max(1, len(kws))

        ctrl_score = style_score(control_resp.generated_text, style_hint)
        treat_score = style_score(treatment_resp.generated_text, style_hint)

        if treat_score > ctrl_score:
            winner = ABGroup.TREATMENT
        elif ctrl_score > treat_score:
            winner = ABGroup.CONTROL
        else:
            winner = None  # 무승부

        result = ABComparisonResult(
            comparison_id=str(uuid.uuid4()),
            prompt=prompt,
            control_response=control_resp,
            treatment_response=treatment_resp,
            winner=winner,
            metrics={
                "control_style_score": ctrl_score,
                "treatment_style_score": treat_score,
                "control_tokens": control_resp.token_count,
                "treatment_tokens": treatment_resp.token_count,
                "latency_delta_ms": treatment_resp.latency_ms - control_resp.latency_ms,
            },
            compared_at=datetime.now(timezone.utc).isoformat(),
        )
        self._ab_results.append(result)
        return result

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        by_tier: dict[str, int] = {}
        for r in self._responses:
            by_tier[r.serving_tier.value] = by_tier.get(r.serving_tier.value, 0) + 1
        ab_wins: dict[str, int] = {"control": 0, "treatment": 0, "tie": 0}
        for ab in self._ab_results:
            if ab.winner == ABGroup.CONTROL:
                ab_wins["control"] += 1
            elif ab.winner == ABGroup.TREATMENT:
                ab_wins["treatment"] += 1
            else:
                ab_wins["tie"] += 1
        return {
            "total_requests": len(self._responses),
            "by_tier": by_tier,
            "canary_pct": self._canary_pct,
            "active_version_id": self._active_version_id,
            "ab_comparisons": len(self._ab_results),
            "ab_wins": ab_wins,
        }
