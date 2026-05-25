"""literary_system/serving/model_serving_endpoint.py

ModelServingEndpoint v1.0 — FastAPI 기반 모델 서빙 엔드포인트
ADR-065 참조.

역할:
    /model_card  엔드포인트를 통해 현재 서빙 중인 모델 정보를
    JSON으로 노출한다. 실제 HTTP 서버 없이도 단위 테스트가
    가능하도록 FastAPI 의존성을 소프트-임포트로 처리한다.

LLM-0 원칙: 외부 LLM API 호출 없음.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# FastAPI 소프트-임포트 (설치 없이도 단위 테스트 가능)
# ---------------------------------------------------------------------------

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore[assignment,misc]
    JSONResponse = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------


@dataclass
class ModelCard:
    """모델 카드 — /model_card 응답 스키마.

    Args:
        model_id: 모델 식별자.
        version: 모델 버전 문자열.
        framework: 학습 프레임워크 (예: "PPO/TRL").
        training_method: 학습 방법 설명.
        reward_threshold: 적용된 보상 임계값.
        gate_passed: 릴리즈 Gate 통과 여부.
        canary_stage: 현재 Canary 단계 (0~3).
        traffic_pct: 현재 서빙 트래픽 비율 (%).
        tags: 부가 태그 목록.
        metadata: 추가 메타데이터.
    """

    model_id: str = "default-model"
    version: str = "1.0.0"
    framework: str = "PPO/TRL"
    training_method: str = "RLHF"
    reward_threshold: float = 0.75
    gate_passed: bool = False
    canary_stage: int = 0
    traffic_pct: int = 5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환한다."""
        return asdict(self)


@dataclass
class EndpointConfig:
    """ModelServingEndpoint 설정.

    Args:
        host: 서버 호스트 (기본값 "0.0.0.0").
        port: 서버 포트 (기본값 8080).
        prefix: API 경로 prefix.
    """

    host: str = "0.0.0.0"
    port: int = 8080
    prefix: str = "/api/v1"


# ---------------------------------------------------------------------------
# 핵심 엔드포인트
# ---------------------------------------------------------------------------


class ModelServingEndpoint:
    """FastAPI 기반 모델 서빙 엔드포인트.

    FastAPI 미설치 환경에서는 get_model_card() 메서드만 사용 가능하다.

    사용 예::

        card = ModelCard(model_id="ppo-v1", gate_passed=True, canary_stage=2, traffic_pct=50)
        endpoint = ModelServingEndpoint(card)
        result = endpoint.get_model_card()
        # result["model_id"] == "ppo-v1"
    """

    def __init__(
        self,
        model_card: Optional[ModelCard] = None,
        config: Optional[EndpointConfig] = None,
    ) -> None:
        self.model_card: ModelCard = model_card or ModelCard()
        self.config: EndpointConfig = config or EndpointConfig()
        self._app: Any = None  # FastAPI 앱 (lazy init)

    # ------------------------------------------------------------------
    # 모델 카드 갱신
    # ------------------------------------------------------------------

    def update_model_card(self, **kwargs: Any) -> None:
        """모델 카드 필드를 동적으로 갱신한다.

        Args:
            **kwargs: ModelCard 필드명 = 갱신값.

        Raises:
            AttributeError: 존재하지 않는 필드를 지정한 경우.
        """
        for key, value in kwargs.items():
            if not hasattr(self.model_card, key):
                raise AttributeError(
                    f"ModelCard에 '{key}' 필드가 없습니다."
                )
            setattr(self.model_card, key, value)

    # ------------------------------------------------------------------
    # /model_card 핸들러 (순수 파이썬 — HTTP 불필요)
    # ------------------------------------------------------------------

    def get_model_card(self) -> Dict[str, Any]:
        """/model_card GET 핸들러 로직을 직접 반환한다.

        Returns:
            ModelCard 딕셔너리. 항상 다음 키를 포함한다:
            model_id, version, framework, training_method,
            reward_threshold, gate_passed, canary_stage, traffic_pct,
            tags, metadata.
        """
        return self.model_card.to_dict()

    # ------------------------------------------------------------------
    # FastAPI 앱 빌드
    # ------------------------------------------------------------------

    def build_app(self) -> Any:
        """FastAPI 앱을 생성하고 /model_card 라우트를 등록한다.

        Returns:
            FastAPI 앱 인스턴스.

        Raises:
            RuntimeError: FastAPI가 설치되지 않은 경우.
        """
        if not _FASTAPI_AVAILABLE:
            raise RuntimeError(
                "FastAPI가 설치되어 있지 않습니다. "
                "`pip install fastapi` 후 재시도하세요."
            )
        if self._app is None:
            app = FastAPI(title="Literary OS Model Serving")

            endpoint = self  # closure

            @app.get(f"{self.config.prefix}/model_card")
            async def model_card_route() -> JSONResponse:
                return JSONResponse(content=endpoint.get_model_card())

            self._app = app
        return self._app

    # ------------------------------------------------------------------
    # 상태 요약
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """엔드포인트 상태 요약을 반환한다.

        반환 딕셔너리 키:
            model_id (str): 모델 식별자.
            endpoint (str): 경로.
            canary_stage (int): 현재 Canary 단계.
            traffic_pct (int): 현재 트래픽 비율.
            gate_passed (bool): Gate 통과 여부.
            fastapi_available (bool): FastAPI 설치 여부.
        """
        return {
            "model_id": self.model_card.model_id,
            "endpoint": f"{self.config.prefix}/model_card",
            "canary_stage": self.model_card.canary_stage,
            "traffic_pct": self.model_card.traffic_pct,
            "gate_passed": self.model_card.gate_passed,
            "fastapi_available": _FASTAPI_AVAILABLE,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  V621 확장 — OpenAPI SemVer (P-IF-04, ADR-088)
# ══════════════════════════════════════════════════════════════════════════════

#: API 시맨틱 버전 상수 (P-IF-04)
SEMVER_MAJOR: int = 1
SEMVER_MINOR: int = 0
SEMVER_PATCH: int = 0
SEMVER: str = f"{SEMVER_MAJOR}.{SEMVER_MINOR}.{SEMVER_PATCH}"

#: OpenAPI YAML 최소 스키마 (실 서버 없이 단위 테스트 가능)
_OPENAPI_SCHEMA_MINIMAL: dict = {
    "openapi": "3.1.0",
    "info": {
        "title": "Literary OS Model Serving API",
        "version": SEMVER,
        "description": "P-IF-04 OpenAPI SemVer (V621, ADR-088)",
    },
    "paths": {
        "/model_card": {
            "get": {
                "summary": "현재 서빙 모델 카드 반환",
                "operationId": "get_model_card",
                "responses": {
                    "200": {"description": "ModelCard JSON"},
                },
            }
        },
        "/openapi.yaml": {
            "get": {
                "summary": "OpenAPI 스펙 YAML 반환 (P-IF-04)",
                "operationId": "get_openapi_yaml",
                "responses": {
                    "200": {"description": "OpenAPI 3.1 YAML"},
                },
            }
        },
        "/api_version": {
            "get": {
                "summary": "현재 API 시맨틱 버전 반환",
                "operationId": "get_api_version",
                "responses": {
                    "200": {
                        "description": "semver string",
                        "content": {
                            "application/json": {
                                "example": {"semver": "1.0.0"}
                            }
                        },
                    }
                },
            }
        },
    },
}


def get_api_version_response() -> dict:
    """P-IF-04: /api_version 엔드포인트 응답 (FastAPI 없이 단위 테스트 가능).

    Returns:
        {"semver": "1.0.0"}
    """
    return {"semver": SEMVER}


def get_openapi_schema() -> dict:
    """P-IF-04: OpenAPI 3.1 스키마 딕셔너리 반환.

    실 FastAPI 인스턴스 없이 단위 테스트 가능하도록 모듈 레벨 상수를 반환한다.
    """
    return dict(_OPENAPI_SCHEMA_MINIMAL)


def build_app_with_semver() -> Any:
    """P-IF-04: /openapi.yaml + /api_version 엔드포인트가 추가된 FastAPI 앱 반환.

    FastAPI 미설치 환경에서는 RuntimeError.
    """
    if not _FASTAPI_AVAILABLE:
        raise RuntimeError(
            "FastAPI가 설치되어 있지 않습니다. `pip install fastapi` 후 재시도."
        )

    try:
        import yaml as _yaml  # pyyaml
    except ImportError:
        import json as _json  # yaml 미설치 시 JSON 폴백

        def _dump(d: dict) -> str:
            return _json.dumps(d, ensure_ascii=False, indent=2)
    else:
        def _dump(d: dict) -> str:  # type: ignore[misc]
            return _yaml.safe_dump(d, allow_unicode=True)

    from fastapi.responses import PlainTextResponse, JSONResponse as _JSONResponse

    app = FastAPI(
        title="Literary OS Model Serving API",
        version=SEMVER,
        description="P-IF-04 OpenAPI SemVer (V621, ADR-088)",
    )

    @app.get("/openapi.yaml", response_class=PlainTextResponse)
    async def openapi_yaml_route() -> str:
        return _dump(get_openapi_schema())

    @app.get("/api_version")
    async def api_version_route() -> _JSONResponse:
        return _JSONResponse(content=get_api_version_response())

    return app
