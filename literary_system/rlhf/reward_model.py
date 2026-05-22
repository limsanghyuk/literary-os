"""
SP-B.2 (V601) — RewardModel: RLHF 보상 모델

Constitution 5축(drse/debt/arc/tension/prose)을 스칼라 보상 R(scene)으로 변환.

설계 원칙 (ADR-061, Phase B 본안 v2.0):
  - 마커 가중치 상한 0.20 (보상 해킹 방지, B-V2-03)
  - 정규화된 5축 합산 → R ∈ [0.0, 1.0]
  - adv_seeds 인터페이스 (B-V2-03 준비, cycle별 적대적 시드 5종 주입)
  - quality_correlation() hook (D23 보상-품질 상관 검증)
  - LLM-0 원칙: 외부 LLM API 직접 호출 없음

적대적 시드 5종 (B-V2-03):
  1. 마커 스터핑 (marker_stuffing)
  2. 길이 인플레이션 (length_inflation)
  3. 반복 패턴 (repetition_pattern)
  4. 극단 감정 (extreme_emotion)
  5. 장르 이탈 (genre_deviation)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

#: 마커 가중치 상한 (보상 해킹 방지, ADR-061 B-V2-03)
MARKER_WEIGHT_CAP: float = 0.20

#: Constitution 5축 기본 가중치 (LOSConstitution v1.0 기준)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "drse":    0.30,
    "debt":    0.20,
    "arc":     0.20,
    "tension": 0.15,
    "prose":   0.15,
}

#: RLHF 합격 기준 R(scene)
REWARD_THRESHOLD: float = 0.70

#: RLHF 목표 R(scene) (SP-B.2 완료 조건)
REWARD_TARGET: float = 0.75


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

class AxisName(str, Enum):
    DRSE    = "drse"
    DEBT    = "debt"
    ARC     = "arc"
    TENSION = "tension"
    PROSE   = "prose"


@dataclass
class ConstitutionAxisReward:
    """Constitution 단일 축 보상."""
    axis: str
    raw_score: float     # LOSConstitution 원점수 [0.0, 1.0]
    weight: float        # 적용 가중치 (≤ MARKER_WEIGHT_CAP)
    weighted: float      # raw_score × weight
    capped: bool = False # 가중치 상한 적용 여부


@dataclass
class RewardResult:
    """RewardModel.compute() 반환 값."""
    reward: float                              # R(scene) ∈ [0.0, 1.0]
    passed: bool                               # reward ≥ REWARD_THRESHOLD
    axis_rewards: List[ConstitutionAxisReward] # 5축 상세
    text_length: int                           # 입력 텍스트 길이
    adv_penalty: float = 0.0                   # 적대적 패턴 감점 합계
    raw_constitution_score: float = 0.0        # LOSConstitution 원점수 합
    errors: List[str] = field(default_factory=list)

    @property
    def axis_dict(self) -> Dict[str, float]:
        return {r.axis: r.raw_score for r in self.axis_rewards}


@dataclass
class AdversarialSeed:
    """적대적 시드 테스트 결과 (B-V2-03)."""
    seed_type: str       # 5종 중 하나
    text: str            # 적대적 입력
    reward: float        # 계산된 보상
    blocked: bool        # 패널티로 차단됐는지 여부 (reward < REWARD_THRESHOLD)
    penalty_applied: float  # 적용된 감점


# ---------------------------------------------------------------------------
# 적대적 패턴 탐지기
# ---------------------------------------------------------------------------

class _AdversarialDetector:
    """5종 적대적 패턴 감지 + 패널티 계산 (B-V2-03)."""

    # 마커 스터핑: 서술/극적 마커 과도 반복
    _MARKER_PATTERNS = re.compile(
        r"(복선|감정|대사|씬|캐릭터|갈등|반전|클라이맥스){5,}",
        re.UNICODE,
    )

    # 반복 패턴: 동일 구절 3회+ 반복
    _REPETITION_PATTERNS = re.compile(r"(.{10,}?)\1{2,}", re.UNICODE)

    # 극단 감정: 감탄사 과도 사용
    _EXTREME_EMOTION = re.compile(r"[!！?？]{3,}|(?:으악|아악|와아+|헐+){2,}", re.UNICODE)

    def detect(self, text: str) -> Tuple[float, List[str]]:
        """
        텍스트에서 적대적 패턴 탐지.

        Returns:
            (total_penalty, detected_types)
        """
        penalty = 0.0
        detected: List[str] = []

        # 1. 마커 스터핑
        if self._MARKER_PATTERNS.search(text):
            penalty += 0.15
            detected.append("marker_stuffing")

        # 2. 길이 인플레이션 (유효 정보 대비 과도한 길이)
        words = text.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.30 and len(words) > 100:
                penalty += 0.10
                detected.append("length_inflation")

        # 3. 반복 패턴
        if self._REPETITION_PATTERNS.search(text):
            penalty += 0.12
            detected.append("repetition_pattern")

        # 4. 극단 감정
        if self._EXTREME_EMOTION.search(text):
            penalty += 0.08
            detected.append("extreme_emotion")

        # 5. 장르 이탈 (한국 드라마 씬 특화 키워드 극단 부재)
        drama_keywords = ["그가", "그녀가", "바라보", "침묵", "목소리", "눈빛",
                          "마음", "느꼈다", "다가", "돌아"]
        keyword_count = sum(1 for kw in drama_keywords if kw in text)
        if len(text) > 200 and keyword_count == 0:
            penalty += 0.10
            detected.append("genre_deviation")

        return min(penalty, 0.50), detected  # 패널티 상한 0.50


# ---------------------------------------------------------------------------
# 핵심 클래스
# ---------------------------------------------------------------------------

class RewardModel:
    """
    RLHF 보상 모델 — Constitution 5축 → 스칼라 R(scene).

    Usage::

        rm = RewardModel()
        result = rm.compute(scene_text)
        # logger.info(result.reward, result.passed)

    LLM-0 원칙: 외부 LLM API 직접 호출 없음.
    ADR-061 참조.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        marker_weight_cap: float = MARKER_WEIGHT_CAP,
    ) -> None:
        """
        Args:
            weights: 5축 가중치 (None이면 DEFAULT_WEIGHTS 사용)
            marker_weight_cap: 마커 가중치 상한 (보상 해킹 방지)
        """
        self._marker_weight_cap = marker_weight_cap
        self._weights = self._validate_and_cap(
            weights or DEFAULT_WEIGHTS
        )
        self._detector = _AdversarialDetector()

        # 품질 상관 누적 버퍼 (quality_correlation() hook용)
        self._correlation_buffer: List[Tuple[float, float]] = []  # (reward, external_quality)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def compute(self, text: str) -> RewardResult:
        """
        씬 텍스트로부터 R(scene) 계산.

        Args:
            text: 씬 텍스트

        Returns:
            RewardResult
        """
        errors: List[str] = []
        axis_rewards: List[ConstitutionAxisReward] = []

        # Constitution 5축 점수 계산 (LLM-0: 외부 호출 없음)
        axis_scores = self._score_axes(text)

        # 가중 합산
        total_weighted = 0.0
        for axis_name, raw in axis_scores.items():
            w = self._weights.get(axis_name, 0.0)
            weighted = raw * w
            total_weighted += weighted
            axis_rewards.append(ConstitutionAxisReward(
                axis=axis_name,
                raw_score=raw,
                weight=w,
                weighted=weighted,
                capped=(w < (DEFAULT_WEIGHTS.get(axis_name, 0.0))),
            ))

        raw_constitution_score = total_weighted

        # 적대적 패턴 패널티 적용
        adv_penalty, _ = self._detector.detect(text)
        reward = max(0.0, raw_constitution_score - adv_penalty)
        reward = min(1.0, reward)

        return RewardResult(
            reward=reward,
            passed=(reward >= REWARD_THRESHOLD),
            axis_rewards=axis_rewards,
            text_length=len(text),
            adv_penalty=adv_penalty,
            raw_constitution_score=raw_constitution_score,
            errors=errors,
        )

    def compute_batch(self, texts: Sequence[str]) -> List[RewardResult]:
        """복수 씬 텍스트 일괄 처리."""
        return [self.compute(t) for t in texts]

    def test_adversarial_seed(
        self, seed_type: str, text: str
    ) -> AdversarialSeed:
        """
        단일 적대적 시드 테스트 (B-V2-03).

        Args:
            seed_type: 'marker_stuffing' | 'length_inflation' |
                       'repetition_pattern' | 'extreme_emotion' | 'genre_deviation'
            text: 적대적 입력 텍스트

        Returns:
            AdversarialSeed
        """
        result = self.compute(text)
        return AdversarialSeed(
            seed_type=seed_type,
            text=text,
            reward=result.reward,
            blocked=(not result.passed),
            penalty_applied=result.adv_penalty,
        )

    def run_adversarial_suite(
        self, seeds: List[Tuple[str, str]]
    ) -> List[AdversarialSeed]:
        """
        적대적 시드 5종 전체 실행 (B-V2-03).

        Args:
            seeds: [(seed_type, text), ...]

        Returns:
            List[AdversarialSeed] — 차단 여부 포함
        """
        return [self.test_adversarial_seed(st, txt) for st, txt in seeds]

    def quality_correlation(
        self, reward: float, external_quality: float
    ) -> float:
        """
        보상-품질 상관 측정 hook (D23).

        보상 스칼라와 외부 품질 측정치(예: 인간 평가 점수) 간의
        Pearson 상관계수를 누적 버퍼 기반으로 반환.

        Args:
            reward: R(scene) 값
            external_quality: 외부 품질 점수 [0.0, 1.0]

        Returns:
            Pearson r (버퍼 N < 2이면 0.0)
        """
        self._correlation_buffer.append((reward, external_quality))
        if len(self._correlation_buffer) < 2:
            return 0.0
        return self._pearson_r(self._correlation_buffer)

    def reset_correlation_buffer(self) -> None:
        """품질 상관 버퍼 초기화."""
        self._correlation_buffer.clear()

    def summary(self, results: List[RewardResult]) -> Dict[str, object]:
        """복수 결과 요약 통계."""
        if not results:
            return {"total": 0, "pass_count": 0, "pass_rate": 0.0, "mean_reward": 0.0}
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        mean_reward = sum(r.reward for r in results) / total
        return {
            "total": total,
            "pass_count": passed,
            "pass_rate": passed / total,
            "mean_reward": mean_reward,
            "reward_threshold": REWARD_THRESHOLD,
        }

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _validate_and_cap(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        가중치 검증 + 마커 상한 적용 + 정규화.

        각 축 가중치를 MARKER_WEIGHT_CAP 이하로 클램프 후
        합계 1.0이 되도록 정규화.
        """
        expected = set(DEFAULT_WEIGHTS.keys())
        given = set(weights.keys())
        if given != expected:
            missing = expected - given
            extra = given - expected
            raise ValueError(
                f"가중치 축 불일치. 누락: {missing}, 추가: {extra}"
            )

        total = sum(weights.values())
        if total <= 0:
            raise ValueError("가중치 합이 0 이하입니다.")

        cap = self._marker_weight_cap
        # 1차 정규화
        w = {k: v / total for k, v in weights.items()}

        # 반복 상한 클램프 (고정 추적 방식):
        # 상한 초과 축을 cap에 영구 고정하고, 나머지만 재정규화.
        # 고정된 축은 이후 스케일에서 제외되므로 재초과 없음.
        fixed: Dict[str, float] = {}
        free: Dict[str, float] = dict(w)

        for _ in range(len(weights) + 1):
            over = {k for k, v in free.items() if v > cap + 1e-9}
            if not over:
                break
            for k in over:
                fixed[k] = cap
                del free[k]
            fixed_sum = sum(fixed.values())
            remaining = 1.0 - fixed_sum
            free_total = sum(free.values())
            if free_total <= 0 or remaining <= 0:
                break
            scale = remaining / free_total
            for k in free:
                free[k] *= scale

        # 최종 클램프: 부동소수점 오차로 인한 미세 초과 방지
        merged = {**fixed, **free}
        return {k: min(v, cap) for k, v in merged.items()}

    def _score_axes(self, text: str) -> Dict[str, float]:
        """
        Constitution 5축 점수 계산 (LLM-0: 규칙 기반, 외부 호출 없음).

        LOSConstitution이 있으면 사용, 없으면 규칙 기반 폴백.
        """
        try:
            from literary_system.constitution.los_constitution import LOSConstitution
            const = LOSConstitution()
            full_result = const.score_scene_full(text)
            const_s = {
                "drse":    float(getattr(full_result, "drse",    0.5)),
                "debt":    float(getattr(full_result, "debt",    0.5)),
                "arc":     float(getattr(full_result, "arc",     0.5)),
                "tension": float(getattr(full_result, "tension", 0.5)),
                "prose":   float(getattr(full_result, "prose",   0.5)),
            }
            # 축 점수가 0에 가까운 경우 규칙 기반 점수로 보정
            # (LOSConstitution이 특정 축을 0으로 반환할 때 발생하는 보상 붕괴 방지)
            rule_s = self._rule_based_scores(text)
            return {k: rule_s[k] if v < 0.01 else v for k, v in const_s.items()}
        except Exception:
            # 폴백: 규칙 기반 추정
            return self._rule_based_scores(text)

    def _rule_based_scores(self, text: str) -> Dict[str, float]:
        """규칙 기반 5축 추정 (LOSConstitution 불가 시 폴백)."""
        length = len(text)
        words  = text.split()
        n_words = max(len(words), 1)
        unique_ratio = len(set(words)) / n_words

        # drse: 텍스트 밀도 (문장 다양성)
        drse = min(1.0, unique_ratio * 1.5)

        # debt: 서사 부채 추정 (반복 적을수록 낮은 부채)
        debt = 1.0 - min(1.0, (1.0 - unique_ratio) * 2.0)

        # arc: 캐릭터 아크 (키워드 기반 + 길이 보조)
        arc_keywords = [
            "결심", "변화", "깨달음", "결정", "각오", "예감",
            "달라", "새로운", "선택", "포기", "다짐", "각성",
            "오래된", "마침내", "드디어",
        ]
        arc_kw_count = sum(1 for kw in arc_keywords if kw in text)
        arc_kw_score = min(1.0, arc_kw_count / 3.0)
        arc_len_score = min(1.0, length / 400.0)
        arc = max(arc_kw_score, arc_len_score)

        # tension: 긴장감 (감정·대립 어휘 밀도)
        tension_words = [
            "갈등", "위기", "충돌", "두려움", "결단", "반전",
            "절박", "분노", "슬픔", "기쁨", "놀라", "긴장감",
            "긴장", "대치", "맞서", "침묵", "눈물",
        ]
        tension_count = sum(1 for w in tension_words if w in text)
        tension = min(1.0, tension_count / 3.0)

        # prose: 문장 품질 (문장 수 / 총 길이 비율)
        sentences = re.split(r"[.。!！?？]", text)
        n_sent = max(len([s for s in sentences if s.strip()]), 1)
        avg_sent_len = length / n_sent
        prose = max(0.0, min(1.0, 1.0 - abs(avg_sent_len - 80) / 200.0))

        return {
            "drse": drse,
            "debt": debt,
            "arc": arc,
            "tension": tension,
            "prose": prose,
        }

    @staticmethod
    def _pearson_r(pairs: List[Tuple[float, float]]) -> float:
        """Pearson 상관계수 계산."""
        n = len(pairs)
        if n < 2:
            return 0.0
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
        den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
        if den_x == 0 or den_y == 0:
            return 0.0
        return num / (den_x * den_y)
