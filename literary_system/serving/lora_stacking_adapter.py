"""
V611 LoRAStackingAdapter — Multi-LoRA 스태킹 인터페이스

책임:
- 장르별 LoRA 가중치 등록·관리
- 복수 LoRA 가중치 선형 합산 (stacking)
- MultiWorkCIMV2 reward_weighted_global_weight 기반 자동 계수 계산
- 스택 유효성 검증 (계수 합 ≤ 1.0 + ε)
- 모델 적용 인터페이스 (apply_to_model: LLM-0 스텁)

스태킹 공식:
    merged[layer][key] = Σ_i (coeff_i * weight_i[layer][key])
    단, Σ coeff_i = 1.0

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .multi_work_cim_v2 import MultiWorkCIMV2

# 허용 오차
_COEFF_SUM_TOLERANCE = 1e-6


@dataclass
class LoRAWeight:
    """단일 LoRA 가중치 레코드.

    weight_data: { layer_name: { param_key: float } }
    형태로 LoRA 델타 가중치를 표현 (실제 텐서 대신 float 맵).
    """
    weight_id: str                          # 고유 식별자
    genre: str                              # 연결된 장르
    version: str                            # 모델 버전
    weight_data: Dict[str, Dict[str, float]]  # layer → param → 값
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def layer_names(self) -> List[str]:
        """등록된 레이어 이름 목록."""
        return list(self.weight_data.keys())

    def param_count(self) -> int:
        """전체 파라미터 수."""
        return sum(len(v) for v in self.weight_data.values())


@dataclass
class StackResult:
    """스태킹 결과."""
    merged_weights: Dict[str, Dict[str, float]]  # layer → param → 합산 값
    coefficients: Dict[str, float]               # weight_id → 계수
    coeff_sum: float                             # 계수 합 (≈ 1.0)
    source_weight_ids: List[str]
    timestamp: float = field(default_factory=time.time)


class LoRAStackingAdapter:
    """Multi-LoRA 스태킹 어댑터 (V611).

    - LoRA 가중치 등록·조회
    - 수동 계수 또는 CIM v2 기반 자동 계수로 스태킹
    - 스택 결과 이력 관리

    LLM-0: 외부 LLM 호출 없음.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        cim_v2: Optional["MultiWorkCIMV2"] = None,
    ) -> None:
        self._weights: Dict[str, LoRAWeight] = {}  # weight_id → LoRAWeight
        self._genre_index: Dict[str, List[str]] = {}  # genre → [weight_id]
        self._stack_history: List[StackResult] = []
        self._cim_v2 = cim_v2
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 가중치 등록·조회
    # ------------------------------------------------------------------ #

    def register(self, lora: LoRAWeight, overwrite: bool = False) -> None:
        """LoRA 가중치 등록.

        Args:
            lora:      LoRAWeight 인스턴스
            overwrite: True이면 동일 weight_id 덮어쓰기

        Raises:
            KeyError: overwrite=False이고 이미 존재하는 weight_id
        """
        with self._lock:
            if lora.weight_id in self._weights and not overwrite:
                raise KeyError(f"LoRA weight already exists: {lora.weight_id}")
            self._weights[lora.weight_id] = lora
            self._genre_index.setdefault(lora.genre, [])
            if lora.weight_id not in self._genre_index[lora.genre]:
                self._genre_index[lora.genre].append(lora.weight_id)

    def get(self, weight_id: str) -> Optional[LoRAWeight]:
        """weight_id로 LoRA 조회."""
        return self._weights.get(weight_id)

    def list_by_genre(self, genre: str) -> List[LoRAWeight]:
        """장르별 LoRA 목록."""
        ids = self._genre_index.get(genre, [])
        return [self._weights[i] for i in ids if i in self._weights]

    def list_genres(self) -> List[str]:
        """등록된 장르 목록."""
        return list(self._genre_index.keys())

    # ------------------------------------------------------------------ #
    # 스태킹
    # ------------------------------------------------------------------ #

    def stack(
        self,
        weight_ids: List[str],
        coefficients: List[float],
    ) -> StackResult:
        """수동 계수로 복수 LoRA 가중치 선형 합산.

        merged[layer][key] = Σ_i (coeff_i * weight_i[layer][key])

        Args:
            weight_ids:   스태킹할 LoRAWeight ID 목록
            coefficients: 각 LoRAWeight에 대한 계수 목록 (Σ 반드시 ≈ 1.0)

        Returns:
            StackResult

        Raises:
            KeyError:   weight_id 미존재
            ValueError: 개수 불일치 또는 계수 합이 1.0을 벗어남
        """
        if len(weight_ids) != len(coefficients):
            raise ValueError(
                f"weight_ids({len(weight_ids)})와 coefficients({len(coefficients)}) 개수 불일치"
            )
        coeff_sum = sum(coefficients)
        if abs(coeff_sum - 1.0) > _COEFF_SUM_TOLERANCE:
            raise ValueError(
                f"계수 합이 1.0이어야 합니다. 현재: {coeff_sum:.6f}"
            )
        if any(c < 0.0 for c in coefficients):
            raise ValueError("계수는 0.0 이상이어야 합니다.")

        with self._lock:
            loras = []
            for wid in weight_ids:
                lora = self._weights.get(wid)
                if lora is None:
                    raise KeyError(f"LoRA weight not found: {wid}")
                loras.append(lora)

            # 합산
            merged: Dict[str, Dict[str, float]] = {}
            for lora, coeff in zip(loras, coefficients):
                for layer, params in lora.weight_data.items():
                    if layer not in merged:
                        merged[layer] = {}
                    for key, val in params.items():
                        merged[layer][key] = merged[layer].get(key, 0.0) + coeff * val

            # 소수점 정리
            for layer in merged:
                for key in merged[layer]:
                    merged[layer][key] = round(merged[layer][key], 8)

            result = StackResult(
                merged_weights=merged,
                coefficients=dict(zip(weight_ids, coefficients)),
                coeff_sum=coeff_sum,
                source_weight_ids=list(weight_ids),
            )
            self._stack_history.append(result)
            return result

    def genre_stack(
        self,
        genres: List[str],
        project_id: str,
        normalize: bool = True,
    ) -> StackResult:
        """장르 목록 + CIM v2 보상 기반 자동 계수 스태킹.

        각 장르의 첫 번째 등록 LoRA를 사용하며,
        CIM v2 reward_weighted_global_weight를 계수로 활용.
        CIM v2가 없으면 균등 계수 사용.

        Args:
            genres:     스태킹할 장르 목록 (각 장르에 등록된 LoRA 必)
            project_id: CIM 조회용 프로젝트 ID
            normalize:  True이면 계수 합이 1.0이 되도록 정규화

        Returns:
            StackResult

        Raises:
            KeyError:   장르에 등록된 LoRA 없음
            ValueError: genres 비어 있음
        """
        if not genres:
            raise ValueError("genres가 비어 있습니다.")

        with self._lock:
            weight_ids: List[str] = []
            raw_coeffs: List[float] = []

            for genre in genres:
                ids = self._genre_index.get(genre, [])
                if not ids:
                    raise KeyError(f"장르에 등록된 LoRA 없음: {genre}")
                weight_ids.append(ids[0])  # 최초 등록 LoRA 사용

                # CIM v2 보상 계수
                coeff = 1.0  # 기본값
                if self._cim_v2 is not None:
                    try:
                        coeff = max(0.01, self._cim_v2.reward_weighted_global_weight(project_id))
                    except Exception:
                        coeff = 1.0
                raw_coeffs.append(coeff)

            # 정규화
            total = sum(raw_coeffs)
            if normalize and total > 0:
                coefficients = [c / total for c in raw_coeffs]
            else:
                coefficients = raw_coeffs

        return self.stack(weight_ids, coefficients)

    def normalize_coefficients(
        self,
        weight_ids: List[str],
        raw_coeffs: List[float],
    ) -> List[float]:
        """계수를 합 1.0으로 정규화."""
        total = sum(raw_coeffs)
        if total <= 0:
            n = len(raw_coeffs)
            return [1.0 / n] * n
        return [c / total for c in raw_coeffs]

    # ------------------------------------------------------------------ #
    # 모델 적용 (LLM-0 스텁)
    # ------------------------------------------------------------------ #

    def apply_to_model(
        self,
        stack_result: StackResult,
        model_id: str = "base",
    ) -> Dict[str, Any]:
        """스태킹 결과를 모델에 적용 (스텁).

        실제 GPU/텐서 연산은 외부 서빙 레이어에서 수행.
        현재는 적용 계획 메타데이터를 반환.

        Returns:
            적용 계획 dict (layer_count, param_count, model_id 포함)
        """
        total_params = sum(
            len(params) for params in stack_result.merged_weights.values()
        )
        return {
            "model_id": model_id,
            "layers_applied": len(stack_result.merged_weights),
            "params_applied": total_params,
            "coefficients": stack_result.coefficients,
            "applied_at": time.time(),
            "status": "stub_ok",  # 실제 적용 시 "applied"로 변경
        }

    # ------------------------------------------------------------------ #
    # 이력·통계
    # ------------------------------------------------------------------ #

    def stack_history(self) -> List[StackResult]:
        """스태킹 이력 전체 반환."""
        with self._lock:
            return list(self._stack_history)

    def stats(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "registered_weights": len(self._weights),
            "genres": self.list_genres(),
            "stack_history_count": len(self._stack_history),
            "has_cim_v2": self._cim_v2 is not None,
        }
