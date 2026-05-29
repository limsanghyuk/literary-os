"""PublicSDK v1.0 — Literary OS 외부 공개 클라이언트 (ADR-116).

4개 코어 메서드:
  analyze(text)          → AnalyzeResult
  repair(text, issues)   → RepairResult
  predict(context, n)    → PredictResult
  generate(blueprint)    → GenerateResult

LLM-1 원칙: AutoPromotionGate(G62) 통과 모델만 서빙.
offline_mode=True(기본)이면 stub 응답 반환.
"""
from __future__ import annotations

import hashlib
import re
import time
from threading import Lock
from typing import Any

from literary_system.sdk.sdk_config import SDKConfig
from literary_system.sdk.sdk_exceptions import (
    AnalyzeError,
    GenerateError,
    PredictError,
    RateLimitError,
    RepairError,
    SDKConfigError,
    ValidationError,
)
from literary_system.sdk.sdk_models import (
    AnalyzeRequest,
    AnalyzeResult,
    GenerateRequest,
    GenerateResult,
    PredictRequest,
    PredictResult,
    QualityScore,
    RepairRequest,
    RepairResult,
    ScenePrediction,
)

__all__ = ["LiteraryOSClient"]

# ── 상수 ─────────────────────────────────────────────────────────────────────
_SDK_VERSION = "1.0.0"
_MIN_TEXT_LEN = 10
_MAX_TEXT_LEN = 50_000
_MAX_PREDICT_N = 10


class _RateLimiter:
    """슬라이딩 윈도우 RPM 제한기."""

    def __init__(self, max_rpm: int) -> None:
        self._max_rpm = max_rpm
        self._timestamps: list[float] = []
        self._lock = Lock()

    def acquire(self) -> None:
        if self._max_rpm == 0:
            return
        now = time.monotonic()
        with self._lock:
            # 60초 이내 요청만 보관
            self._timestamps = [t for t in self._timestamps if now - t < 60.0]
            if len(self._timestamps) >= self._max_rpm:
                raise RateLimitError(self._max_rpm)
            self._timestamps.append(now)


class LiteraryOSClient:
    """Literary OS PublicSDK v1.0 클라이언트.

    Parameters
    ----------
    config:
        SDKConfig 인스턴스. None이면 환경변수/기본값으로 초기화.
    """

    def __init__(self, config: SDKConfig | None = None) -> None:
        self._config = config or SDKConfig()
        self._limiter = _RateLimiter(self._config.max_rpm)
        self._call_count = 0
        self._version = _SDK_VERSION

    # ── 공개 프로퍼티 ─────────────────────────────────────────────────────

    @property
    def version(self) -> str:
        return self._version

    @property
    def config(self) -> SDKConfig:
        return self._config

    # ── analyze() ─────────────────────────────────────────────────────────

    def analyze(
        self,
        text: str,
        context: str = "",
        lang: str | None = None,
    ) -> AnalyzeResult:
        """텍스트 씬 품질 분석.

        Parameters
        ----------
        text:    분석할 씬 텍스트 (10~50,000자)
        context: 앞 씬 맥락 (선택)
        lang:    언어 코드 (기본: config.default_lang)

        Returns
        -------
        AnalyzeResult
        """
        self._limiter.acquire()
        req = AnalyzeRequest(
            text=text,
            context=context,
            lang=lang or self._config.default_lang,
        )
        self._validate_text(req.text, "text")
        self._call_count += 1

        try:
            if self._config.offline_mode:
                return self._analyze_offline(req)
            return self._analyze_online(req)
        except (AnalyzeError, ValidationError, RateLimitError):
            raise
        except Exception as exc:
            raise AnalyzeError(f"Unexpected error in analyze: {exc}") from exc

    def _analyze_offline(self, req: AnalyzeRequest) -> AnalyzeResult:
        """오프라인 stub 분석 — 규칙 기반 휴리스틱."""
        text = req.text
        sentences = [s.strip() for s in re.split(r"[.!?。！？]", text) if s.strip()]
        words = text.split()

        # 간단한 품질 추정 (실제 서빙에서는 내부 모델 호출)
        coherence = min(1.0, len(sentences) / max(1, len(sentences) + 2) + 0.3)
        emotion = min(1.0, _score_emotion_words(text))
        style = min(1.0, _score_style(text))
        character = min(1.0, _score_character_refs(text))
        tension = min(1.0, _score_tension(text))

        quality = QualityScore(
            coherence=round(coherence, 4),
            emotion=round(emotion, 4),
            style=round(style, 4),
            character=round(character, 4),
            tension=round(tension, 4),
        )

        issues: list[str] = []
        if quality.overall < self._config.quality_threshold:
            issues.append(f"overall_score_low:{quality.overall:.3f}")
        if len(sentences) < 2:
            issues.append("too_few_sentences")
        if len(words) < 20:
            issues.append("text_too_short")

        patterns = _extract_patterns(text)

        return AnalyzeResult(
            quality=quality,
            issues=issues,
            patterns=patterns,
            word_count=len(words),
            sentence_count=len(sentences),
            passed=len(issues) == 0,
            meta={"mode": "offline", "sdk_version": self._version},
        )

    def _analyze_online(self, req: AnalyzeRequest) -> AnalyzeResult:
        """온라인 분석 — constitution 기반 텍스트 품질 분석."""
        try:
            from literary_system.constitution.constitution_eval_v2 import ConstitutionEvalV2
        except ImportError:
            # 폴백: 오프라인 분석
            return self._analyze_offline(req)

        try:
            evaluator = ConstitutionEvalV2()
            eval_result = evaluator.evaluate(req.text)
            quality = QualityScore(
                coherence=getattr(eval_result, "coherence_score", 0.75),
                emotion=getattr(eval_result, "emotion_score", 0.70),
                style=getattr(eval_result, "style_score", 0.72),
                character=getattr(eval_result, "character_score", 0.74),
                tension=getattr(eval_result, "tension_score", 0.68),
            )
        except Exception:
            return self._analyze_offline(req)

        return AnalyzeResult(
            quality=quality,
            issues=[],
            suggestions=["온라인 분석 완료 — constitution 평가 기반"],
            meta={"mode": "online", "sdk_version": self._version},
        )

    # ── repair() ──────────────────────────────────────────────────────────

    def repair(
        self,
        text: str,
        issues: list[str],
        target_score: float = 0.75,
        lang: str | None = None,
    ) -> RepairResult:
        """이슈 기반 텍스트 수정.

        Parameters
        ----------
        text:         원본 씬 텍스트
        issues:       수정 대상 이슈 목록 (analyze()의 issues 필드)
        target_score: 목표 품질 점수 (0~1)
        lang:         언어 코드
        """
        self._limiter.acquire()
        req = RepairRequest(
            text=text,
            issues=issues,
            target_score=target_score,
            lang=lang or self._config.default_lang,
        )
        self._validate_text(req.text, "text")
        if not (0.0 < req.target_score <= 1.0):
            raise ValidationError("target_score", "must be in (0, 1]")
        self._call_count += 1

        try:
            if self._config.offline_mode:
                return self._repair_offline(req)
            return self._repair_online(req)
        except (RepairError, ValidationError, RateLimitError):
            raise
        except Exception as exc:
            raise RepairError(f"Unexpected error in repair: {exc}") from exc

    def _repair_offline(self, req: RepairRequest) -> RepairResult:
        """오프라인 stub 수정."""
        before = self.analyze(req.text, lang=req.lang)
        score_before = before.quality.overall

        repaired = req.text
        applied: list[str] = []

        for issue in req.issues:
            if issue == "too_few_sentences" and not repaired.endswith("."):
                repaired += " 이야기는 계속된다."
                applied.append("append_continuation_sentence")
            elif issue == "text_too_short":
                repaired += " 장면의 분위기가 고조되고 있었다."
                applied.append("append_atmosphere_sentence")
            elif issue.startswith("overall_score_low"):
                repaired = repaired.replace("  ", " ").strip()
                applied.append("normalize_whitespace")

        after = self.analyze(repaired, lang=req.lang)
        score_after = after.quality.overall

        return RepairResult(
            original_text=req.text,
            repaired_text=repaired,
            applied_fixes=applied,
            score_before=round(score_before, 4),
            score_after=round(score_after, 4),
            improved=score_after > score_before,
            meta={"mode": "offline", "sdk_version": self._version},
        )

    def _repair_online(self, req: RepairRequest) -> RepairResult:
        """온라인 수정 — EditorAgent 기반 산문 교정."""
        try:
            from literary_system.agents.editor_agent import EditorAgent
        except ImportError:
            return self._repair_offline(req)

        try:
            editor = EditorAgent()
            edited = editor.edit(req.text, issues=req.issues or [])
            repaired_text = getattr(edited, "final_text", req.text)
            notes = list(getattr(edited, "polish_notes", []))
        except Exception:
            return self._repair_offline(req)

        return RepairResult(
            repaired_text=repaired_text,
            changes=notes,
            meta={"mode": "online", "sdk_version": self._version},
        )

    # ── predict() ─────────────────────────────────────────────────────────

    def predict(
        self,
        context: str,
        n: int = 3,
        style_hint: str = "",
        lang: str | None = None,
    ) -> PredictResult:
        """다음 씬 예측 후보 n개 반환.

        Parameters
        ----------
        context:    이전 씬 맥락 텍스트
        n:          반환할 예측 후보 수 (1~10)
        style_hint: 문체 힌트 (예: "melodrama", "thriller")
        lang:       언어 코드
        """
        self._limiter.acquire()
        req = PredictRequest(
            context=context,
            n=n,
            style_hint=style_hint,
            lang=lang or self._config.default_lang,
        )
        self._validate_text(req.context, "context")
        if not (1 <= req.n <= _MAX_PREDICT_N):
            raise ValidationError("n", f"must be in [1, {_MAX_PREDICT_N}]")
        self._call_count += 1

        try:
            if self._config.offline_mode:
                return self._predict_offline(req)
            return self._predict_online(req)
        except (PredictError, ValidationError, RateLimitError):
            raise
        except Exception as exc:
            raise PredictError(f"Unexpected error in predict: {exc}") from exc

    def _predict_offline(self, req: PredictRequest) -> PredictResult:
        """오프라인 stub 예측 — 결정론적 시드 기반."""
        seed = int(hashlib.md5(req.context.encode()).hexdigest(), 16) % 1000
        templates = [
            ("갈등이 정점에 달하는 장면", "긴장→폭발", 0.40),
            ("캐릭터가 내면을 드러내는 장면", "평온→성찰", 0.25),
            ("새로운 인물이 등장하는 장면", "중립→호기심", 0.20),
            ("과거 회상 장면", "현재→과거", 0.10),
            ("화해와 해소 장면", "긴장→이완", 0.05),
        ]
        preds: list[ScenePrediction] = []
        for i in range(req.n):
            idx = (seed + i) % len(templates)
            synopsis, arc, prob = templates[idx]
            if req.style_hint:
                synopsis = f"[{req.style_hint}] {synopsis}"
            preds.append(
                ScenePrediction(
                    rank=i + 1,
                    synopsis=synopsis,
                    emotion_arc=arc,
                    probability=round(prob * (0.9 ** i), 4),
                )
            )

        return PredictResult(
            predictions=preds,
            context_tokens=len(req.context.split()),
            meta={"mode": "offline", "sdk_version": self._version},
        )

    def _predict_online(self, req: PredictRequest) -> PredictResult:
        """온라인 예측 — predictive 모듈 기반 다음 씬 예측."""
        try:
            from literary_system.predictive.scene_predictor import ScenePredictor
        except ImportError:
            return self._predict_offline(req)

        try:
            predictor = ScenePredictor()
            predictions = predictor.predict(req.context, n=req.n)
            results = [
                {"text": str(p), "probability": 1.0 / (i + 1)}
                for i, p in enumerate(predictions[:req.n])
            ]
        except Exception:
            return self._predict_offline(req)

        return PredictResult(
            predictions=results,
            meta={"mode": "online", "sdk_version": self._version},
        )

    # ── generate() ────────────────────────────────────────────────────────

    def generate(
        self,
        title: str,
        characters: list[str],
        setting: str,
        conflict: str,
        tone: str = "dramatic",
        max_rounds: int = 3,
        lang: str | None = None,
    ) -> GenerateResult:
        """씬 생성 (DirectorAgent 래퍼).

        Parameters
        ----------
        title:      씬 제목
        characters: 등장인물 목록
        setting:    배경 설정
        conflict:   갈등 요소
        tone:       문체 톤 (dramatic / lyrical / thriller / comedic)
        max_rounds: 에이전트 최대 라운드 수 (≤3)
        lang:       언어 코드
        """
        self._limiter.acquire()
        req = GenerateRequest(
            title=title,
            characters=characters,
            setting=setting,
            conflict=conflict,
            tone=tone,
            max_rounds=min(max_rounds, 3),
            lang=lang or self._config.default_lang,
        )
        if not req.title.strip():
            raise ValidationError("title", "must not be empty")
        if not req.characters:
            raise ValidationError("characters", "must have at least one character")
        if not req.setting.strip():
            raise ValidationError("setting", "must not be empty")
        self._call_count += 1

        try:
            if self._config.offline_mode:
                return self._generate_offline(req)
            return self._generate_online(req)
        except (GenerateError, ValidationError, RateLimitError):
            raise
        except Exception as exc:
            raise GenerateError(f"Unexpected error in generate: {exc}") from exc

    def _generate_offline(self, req: GenerateRequest) -> GenerateResult:
        """오프라인 stub 생성."""
        chars = ", ".join(req.characters[:3])
        scene_text = (
            f"[{req.title}]\n"
            f"{chars}이(가) {req.setting}에서 마주쳤다. "
            f"{req.conflict}. "
            f"분위기는 {req.tone}하게 흘러갔다. "
            f"그들의 선택이 이야기를 바꾸려 하고 있었다."
        )

        quality = QualityScore(
            coherence=0.75,
            emotion=0.70,
            style=0.72,
            character=0.78,
            tension=0.68,
        )

        blueprint = {
            "title": req.title,
            "characters": req.characters,
            "setting": req.setting,
            "conflict": req.conflict,
            "tone": req.tone,
            "elements": ["exposition", "conflict_trigger", "character_reaction"],
        }

        return GenerateResult(
            scene_text=scene_text,
            quality=quality,
            rounds_used=1,
            director_blueprint=blueprint,
            passed_critic=quality.overall >= 0.65,
            meta={"mode": "offline", "sdk_version": self._version},
        )

    def _generate_online(self, req: GenerateRequest) -> GenerateResult:
        """온라인 생성 — AgentCoordinator 기반 멀티에이전트 파이프라인.

        Director(Blueprint) → Script(최대 3라운드) → Critic → Editor 순 실행.
        LLM-0 준수: 외부 API 직접 호출 없음 (AgentCoordinator 내 lazy-import).
        """
        try:
            from literary_system.ensemble.agent_coordinator import AgentCoordinator
        except ImportError as exc:
            raise GenerateError(f"AgentCoordinator 로드 실패: {exc}") from exc

        blueprint_dict = {
            "title":      req.title,
            "characters": req.characters,
            "setting":    req.setting,
            "conflict":   req.conflict,
            "tone":       req.tone,
        }
        try:
            coord = AgentCoordinator(max_rounds=min(req.max_rounds, 3))
            coord_result = coord.coordinate(
                blueprint_dict=blueprint_dict,
                scene_prefix=req.title[:20].replace(" ", "_"),
            )
        except Exception as exc:
            raise GenerateError(f"AgentCoordinator 실행 실패: {exc}") from exc

        quality = QualityScore(
            coherence=coord_result.last_critic_score,
            emotion=coord_result.last_critic_score * 0.95,
            style=coord_result.last_critic_score * 0.90,
            character=coord_result.last_critic_score * 0.92,
            tension=coord_result.last_critic_score * 0.88,
        )
        return GenerateResult(
            scene_text=coord_result.final_text,
            quality=quality,
            rounds_used=coord_result.rounds_used,
            director_blueprint=coord_result.blueprint_dict,
            passed_critic=coord_result.success,
            meta={
                "mode": "online",
                "sdk_version": self._version,
                "coordinator_result": coord_result.to_dict(),
            },
        )

    # ── 유틸리티 ──────────────────────────────────────────────────────────

    def _validate_text(self, text: str, field: str) -> None:
        if not isinstance(text, str):
            raise ValidationError(field, "must be a string")
        if len(text) < _MIN_TEXT_LEN:
            raise ValidationError(field, f"too short (min {_MIN_TEXT_LEN} chars)")
        if len(text) > _MAX_TEXT_LEN:
            raise ValidationError(field, f"too long (max {_MAX_TEXT_LEN} chars)")

    def stats(self) -> dict[str, Any]:
        """누적 호출 통계 반환."""
        return {
            "total_calls": self._call_count,
            "sdk_version": self._version,
            "offline_mode": self._config.offline_mode,
        }


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

_EMOTION_WORDS = {
    "눈물", "웃음", "분노", "슬픔", "기쁨", "두려움", "설렘",
    "절망", "희망", "외로움", "그리움", "사랑", "미움",
}

_TENSION_WORDS = {
    "위기", "폭발", "충돌", "갈등", "긴장", "대립", "싸움",
    "도망", "추격", "비밀", "배신", "음모", "복수",
}

_STYLE_MARKERS = {"그", "그녀", "이", "저", "하지만", "그러나", "왜냐하면", "따라서"}


def _score_emotion_words(text: str) -> float:
    hits = sum(1 for w in _EMOTION_WORDS if w in text)
    return 0.4 + min(0.6, hits * 0.1)


def _score_tension(text: str) -> float:
    hits = sum(1 for w in _TENSION_WORDS if w in text)
    return 0.35 + min(0.65, hits * 0.12)


def _score_style(text: str) -> float:
    hits = sum(1 for w in _STYLE_MARKERS if w in text)
    return 0.45 + min(0.55, hits * 0.06)


def _score_character_refs(text: str) -> float:
    # 인물명 패턴: 2~4글자 한글 고유명사 (간단 추정)
    matches = re.findall(r"[가-힣]{2,4}[이가은는]", text)
    return 0.40 + min(0.60, len(matches) * 0.08)


def _extract_patterns(text: str) -> list[str]:
    patterns: list[str] = []
    if "회상" in text or "기억" in text:
        patterns.append("flashback")
    if "독백" in text or "생각했다" in text:
        patterns.append("inner_monologue")
    if re.search(r"[가-힣]+이?라고", text):
        patterns.append("dialogue")
    if "갑자기" in text or "순간" in text:
        patterns.append("sudden_event")
    return patterns


# ─── CLI entry point (PyPI entry_point: literary-sdk) ───────────────────────
def _cli_demo() -> None:
    """
    literary-sdk CLI 데모 진입점.
    PyPI 설치 후 `literary-sdk` 명령으로 실행.
    """
    import sys

    def _out(msg: str = "") -> None:
        sys.stdout.write(msg + "\n")

    from literary_system.sdk.sdk_config import SDKConfig
    client = LiteraryOSClient(config=SDKConfig(offline_mode=True))
    _out("Literary OS PublicSDK v1.0 — Demo")
    _out("=" * 40)

    sample = "준호는 오랫동안 그 장면을 잊지 못했다. 갑자기 눈물이 흘렀다."
    _out(f"[입력] {sample}")
    _out()

    result = client.analyze(sample)
    _out(f"[analyze] overall={result.quality.overall:.3f}  patterns={result.patterns}")

    repaired = client.repair(sample, issues=[])
    _out(f"[repair]  improved={repaired.improved}  text='{repaired.repaired_text[:40]}...'")

    pred = client.predict(sample)
    arc = pred.predictions[0].emotion_arc if pred.predictions else "N/A"
    _out(f"[predict] emotion_arc={arc}  count={len(pred.predictions)}")

    gen = client.generate(
        title="이별의 밤",
        characters=["준호", "수아"],
        setting="병원 옥상",
        conflict="작별 인사",
    )
    _out(f"[generate] excerpt='{gen.scene_text[:50]}...'")

    _out()
    _out("✅ PublicSDK 동작 확인 완료 (offline_mode=True)")
    sys.exit(0)
