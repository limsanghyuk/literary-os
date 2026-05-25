"""
SP-C.1 (V631) — LOSConstitution v2.0 — Bayesian Weight Optimiser

LOSConstitution v1.0 (ADR-054) 를 상속하여 5축 가중치를 Bayesian Optimisation
(Optuna TPE Sampler) 으로 자동 학습한다.

주요 기능
----------
1. Bayesian Optimisation (Optuna) — w1~w5 탐색 공간 (Dirichlet-like simplex)
2. Entropy 분포 제약 (C-M-05, ADR-098): entropy(w) >= 1.5
   Shannon 엔트로피 H = -Σ wᵢ · log₂(wᵢ) ≥ 1.5
   (5축 최대 ≈ 2.322; 1.5 하한으로 극단 집중 방지)
3. 학습 결과 persistence: JSON 저장/로드 (constitution_weights_v2.json)
4. 완전 LLM-0 준수: 외부 API 호출 없음

ADR-098 참조.
기반: LOSConstitution v1.0 (ADR-054, SP-A.7, V594)
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from literary_system.constitution.los_constitution import (
    ConstitutionWeights,
    ConstitutionSceneScore,
    ConstitutionWorkScore,
    LOSConstitution,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수 및 타입 별칭
# ---------------------------------------------------------------------------

_MIN_ENTROPY: float = 1.5       # C-M-05 하한
_N_TRIALS_DEFAULT: int = 100    # Optuna 기본 trial 수
_AXES: Tuple[str, ...] = ("drse", "debt", "arc", "tension", "prose")

# TrainSample: (장면 텍스트, 목표 점수 0~1)
TrainSample = Tuple[str, float]


# ---------------------------------------------------------------------------
# 엔트로피 헬퍼
# ---------------------------------------------------------------------------

def _shannon_entropy(weights: Sequence[float]) -> float:
    """Shannon 엔트로피 H(w) = -Σ wᵢ · log₂(wᵢ)  (밑 2, bits)."""
    h = 0.0
    for w in weights:
        if w > 1e-9:
            h -= w * math.log2(w)
    return h


def entropy_constraint_pass(weights: ConstitutionWeights, threshold: float = _MIN_ENTROPY) -> bool:
    """
    entropy(w) >= threshold 여부 반환.

    Args:
        weights:   ConstitutionWeights 인스턴스
        threshold: 최솟값 (기본 1.5 bits, C-M-05)

    Returns:
        bool — True if PASS
    """
    vals = list(weights.as_dict().values())
    return _shannon_entropy(vals) >= threshold


# ---------------------------------------------------------------------------
# OptimisationResult
# ---------------------------------------------------------------------------

@dataclass
class OptimisationResult:
    """Bayesian Optimisation 결과 컨테이너."""
    best_weights: ConstitutionWeights
    best_mse: float
    entropy: float
    n_trials: int
    n_pruned: int
    converged: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_weights": self.best_weights.as_dict(),
            "best_mse": self.best_mse,
            "entropy": self.entropy,
            "n_trials": self.n_trials,
            "n_pruned": self.n_pruned,
            "converged": self.converged,
        }


# ---------------------------------------------------------------------------
# LOSConstitutionV2
# ---------------------------------------------------------------------------

class LOSConstitutionV2(LOSConstitution):
    """
    Literary OS 장면 품질 헌법 v2.0 — Bayesian Weight Optimiser 내장.

    V1 대비 변경
    -----------
    - __init__ : 초기 weights + 최적화 이력 관리
    - optimise_weights() : Optuna TPE Sampler 로 w1~w5 탐색
    - entropy_ok         : 현재 weights 의 엔트로피 검사 property
    - save / load        : JSON 영속화

    LLM-0 준수: 외부 LLM API 호출 없음.

    Usage::

        v2 = LOSConstitutionV2()

        # 학습 데이터: [(씬 텍스트, 목표 점수), ...]
        samples = [("장면1 텍스트...", 0.80), ("장면2 텍스트...", 0.65)]

        result = v2.optimise_weights(samples, n_trials=50)
        assert result.converged
        assert result.entropy >= 1.5

        score = v2.score_scene("새 씬 텍스트")

    ADR-098 §3 참조.
    """

    # ── 생성자 ─────────────────────────────────────────────────────────────

    def __init__(
        self,
        weights: Optional[ConstitutionWeights] = None,
        entropy_threshold: float = _MIN_ENTROPY,
    ) -> None:
        """
        Args:
            weights:           초기 weights (None → ADR-054 기본값)
            entropy_threshold: C-M-05 최솟값 (기본 1.5 bits)
        """
        super().__init__(weights)
        self._entropy_threshold = entropy_threshold
        self._optimisation_history: List[OptimisationResult] = []

    # ── entropy 검사 ────────────────────────────────────────────────────────

    @property
    def entropy_ok(self) -> bool:
        """현재 weights 가 entropy 제약을 만족하는지 여부."""
        return entropy_constraint_pass(self._w, self._entropy_threshold)

    @property
    def current_entropy(self) -> float:
        """현재 weights 의 Shannon 엔트로피 (bits)."""
        return _shannon_entropy(list(self._w.as_dict().values()))

    # ── Bayesian Optimisation ───────────────────────────────────────────────

    def optimise_weights(
        self,
        samples: List[TrainSample],
        n_trials: int = _N_TRIALS_DEFAULT,
        seed: Optional[int] = 42,
        verbose: bool = False,
    ) -> OptimisationResult:
        """
        Bayesian Optimisation (Optuna TPE) 으로 5축 가중치를 최적화.

        목적 함수: MSE(predicted_score, target_score) 최소화
        제약: entropy(w) >= _entropy_threshold (위반 시 trial pruning)

        Args:
            samples:   [(텍스트, 목표점수), ...]  최소 1개
            n_trials:  Optuna trial 수 (기본 100)
            seed:      재현성 시드
            verbose:   Optuna 로그 출력 여부

        Returns:
            OptimisationResult — best_weights, best_mse, entropy, 수렴 여부

        Raises:
            ImportError:  optuna 미설치 시
            ValueError:   samples 빈 리스트
        """
        if not samples:
            raise ValueError("optimise_weights: samples 가 비어있습니다.")

        try:
            import optuna  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "LOSConstitutionV2.optimise_weights() 는 optuna 패키지가 필요합니다.\n"
                "설치: pip install optuna --break-system-packages"
            ) from exc

        if not verbose:
            optuna.logging.set_verbosity(optuna.logging.WARNING)

        n_pruned = 0
        _MIN_W = 0.02   # 각 축 최솟값 (합산 0.10 → 나머지 0.90 분배)

        def objective(trial: "optuna.Trial") -> float:
            nonlocal n_pruned

            # ── 5축 가중치 제안 (simplex 투영) ─────────────────────────
            raw = [
                trial.suggest_float(ax, _MIN_W, 1.0)
                for ax in _AXES
            ]
            total = sum(raw)
            w_vals = [v / total for v in raw]

            # ── entropy 제약 검사 (C-M-05) ──────────────────────────────
            h = _shannon_entropy(w_vals)
            if h < self._entropy_threshold:
                n_pruned += 1
                raise optuna.exceptions.TrialPruned(
                    f"entropy={h:.4f} < threshold={self._entropy_threshold}"
                )

            # ── MSE 계산 ────────────────────────────────────────────────
            try:
                tmp_w = ConstitutionWeights(
                    drse=w_vals[0],
                    debt=w_vals[1],
                    arc=w_vals[2],
                    tension=w_vals[3],
                    prose=w_vals[4],
                )
            except ValueError:
                n_pruned += 1
                raise optuna.exceptions.TrialPruned("Invalid weights")

            tmp_constitution = LOSConstitution(weights=tmp_w)
            mse = 0.0
            for text, target in samples:
                pred = tmp_constitution.score_scene(text)
                mse += (pred - target) ** 2
            return mse / len(samples)

        sampler = optuna.samplers.TPESampler(seed=seed)
        study = optuna.create_study(direction="minimize", sampler=sampler)
        study.optimize(objective, n_trials=n_trials, catch=(Exception,))

        # ── 최적 결과 추출 ──────────────────────────────────────────────
        completed = [t for t in study.trials if t.state.name == "COMPLETE"]
        if not completed:
            # 모든 trial이 pruned → 기본값 유지, 수렴 실패
            result = OptimisationResult(
                best_weights=ConstitutionWeights(),
                best_mse=float("inf"),
                entropy=_shannon_entropy(list(ConstitutionWeights().as_dict().values())),
                n_trials=n_trials,
                n_pruned=n_pruned,
                converged=False,
            )
            self._optimisation_history.append(result)
            return result

        best_trial = study.best_trial
        raw_best = [best_trial.params[ax] for ax in _AXES]
        total_best = sum(raw_best)
        w_best = [v / total_best for v in raw_best]

        best_w = ConstitutionWeights(
            drse=w_best[0],
            debt=w_best[1],
            arc=w_best[2],
            tension=w_best[3],
            prose=w_best[4],
        )
        h_best = _shannon_entropy(w_best)
        converged = h_best >= self._entropy_threshold

        # ── weights 갱신 ────────────────────────────────────────────────
        self._w = best_w

        result = OptimisationResult(
            best_weights=best_w,
            best_mse=best_trial.value,
            entropy=h_best,
            n_trials=n_trials,
            n_pruned=n_pruned,
            converged=converged,
        )
        self._optimisation_history.append(result)

        logger.info(
            "V631 LOSConstitutionV2 최적화 완료 | "
            f"MSE={best_trial.value:.6f} | entropy={h_best:.4f} | "
            f"converged={converged} | pruned={n_pruned}/{n_trials}"
        )
        return result

    # ── 최적화 이력 ─────────────────────────────────────────────────────────

    @property
    def optimisation_history(self) -> List[OptimisationResult]:
        """누적 최적화 이력 (읽기 전용)."""
        return list(self._optimisation_history)

    # ── 영속화 ─────────────────────────────────────────────────────────────

    def save(self, path: Union[str, Path]) -> None:
        """
        현재 weights + 이력을 JSON 파일로 저장.

        Args:
            path: 저장 경로 (예: 'constitution_weights_v2.json')
        """
        data: Dict[str, Any] = {
            "version": "2.0",
            "adr": "ADR-098",
            "weights": self._w.as_dict(),
            "entropy_threshold": self._entropy_threshold,
            "entropy_current": self.current_entropy,
            "entropy_ok": self.entropy_ok,
            "history": [r.to_dict() for r in self._optimisation_history],
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"LOSConstitutionV2 weights 저장 → {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "LOSConstitutionV2":
        """
        JSON 파일에서 weights 를 복원한 LOSConstitutionV2 반환.

        Args:
            path: 저장된 JSON 경로

        Returns:
            LOSConstitutionV2 인스턴스
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        w_dict = data["weights"]
        weights = ConstitutionWeights(
            drse=w_dict["drse"],
            debt=w_dict["debt"],
            arc=w_dict["arc"],
            tension=w_dict["tension"],
            prose=w_dict["prose"],
        )
        threshold = data.get("entropy_threshold", _MIN_ENTROPY)
        instance = cls(weights=weights, entropy_threshold=threshold)
        logger.info(f"LOSConstitutionV2 weights 복원 ← {path}")
        return instance
