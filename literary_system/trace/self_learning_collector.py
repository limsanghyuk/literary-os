"""
V325 - SelfLearningCollector  (Phase 4)
씬 생성 결과 자동 누적 → V326 SLM 파인튜닝 데이터셋 기반.

설계 원칙 (P2 외과적 통합):
  - TraceDatasetStore 기존 코드 무수정
  - 독립 JSONL 파일에 V325 확장 레코드 저장
    {scene_id, text, metrics_snapshot, consensus, coeff_snapshot, seq_plan_snapshot}
  - export_as_slm_dataset() → instruction-tuning 포맷 변환
  - LLM 0회 — 완전 로컬
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# SLMRecord 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class SLMRecord:
    """
    V325 학습 데이터 원자 단위.
    SceneRecord + SceneMetrics + MAEResult + coeff_snapshot 통합.
    """
    record_id:        str
    scene_id:         str
    seq_id:           str
    episode_no:       int
    scene_text:       str
    consensus:        bool
    retries:          int
    mae_score:        float
    metrics_snapshot: dict[str, Any]    # SceneMetrics 핵심 필드
    coeff_snapshot:   dict[str, float]  # LearnedCoefficients 스냅샷
    seq_plan_snapshot: dict[str, Any]   # SequencePlan.to_dict()
    created_at:       float = field(default_factory=time.time)
    project_id:       str  = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id":         self.record_id,
            "scene_id":          self.scene_id,
            "seq_id":            self.seq_id,
            "episode_no":        self.episode_no,
            "consensus":         self.consensus,
            "retries":           self.retries,
            "mae_score":         round(self.mae_score, 4),
            "metrics_snapshot":  self.metrics_snapshot,
            "coeff_snapshot":    self.coeff_snapshot,
            "seq_plan_snapshot": self.seq_plan_snapshot,
            "scene_text_len":    len(self.scene_text),
            "created_at":        self.created_at,
            "project_id":        self.project_id,
        }

    def as_slm_pair(self) -> dict[str, Any] | None:
        """
        V326 instruction-tuning 포맷 변환.
        consensus=True인 레코드만 학습 데이터로 사용.
        """
        if not self.consensus:
            return None
        if not self.scene_text.strip():
            return None

        plan = self.seq_plan_snapshot
        instruction = (
            f"[시퀀스 목표] {plan.get('goal', '')}\n"
            f"[막 위치] act{plan.get('act_index', 0)}"
            f"  [긴장도] {plan.get('tension_target', 0.5):.2f}\n"
            f"[MAE 점수] {self.mae_score:.2f}"
            f"  [재시도] {self.retries}회"
        )
        return {
            "record_id":   self.record_id,
            "scene_id":    self.scene_id,
            "instruction": instruction,
            "output":      self.scene_text,
            "quality": {
                "mae_score":    self.mae_score,
                "retries":      self.retries,
                "reader_pull":  self.metrics_snapshot.get("reader_pull", 0.0),
            },
        }


# ────────────────────────────────────────────────────────────────
# SelfLearningCollector
# ────────────────────────────────────────────────────────────────

class SelfLearningCollector:
    """
    SceneGenerationOrchestrator 결과 → SLM 학습 데이터 자동 누적.

    사용 예:
        collector = SelfLearningCollector(store_path="./data/slm_traces")
        collector.collect(scene_record, coeff_snapshot={"reader_pull_weight": 1.1})
        dataset = collector.export_as_slm_dataset()  # V326용
    """

    def __init__(
        self,
        store_path: str | Path = "./data/slm_traces",
        project_id: str = "default",
    ) -> None:
        self._store_path = Path(store_path)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._project_id  = project_id
        self._records:    list[SLMRecord] = []
        self._jsonl_path: Path = self._store_path / "slm_records.jsonl"

    # ── 공개 API ─────────────────────────────────────────────────

    @property
    def record_count(self) -> int:
        return len(self._records)

    @property
    def consensus_count(self) -> int:
        return sum(1 for r in self._records if r.consensus)

    def collect(
        self,
        scene_record:    Any,                       # SceneRecord
        coeff_snapshot:  dict[str, float] | None = None,
        seq_plan:        Any | None = None,          # SequencePlan | None
        episode_no:      int = 1,
    ) -> SLMRecord:
        """
        씬 레코드 수집 + JSONL 저장.

        Args:
            scene_record:   SceneGenerationOrchestrator 반환 SceneRecord
            coeff_snapshot: LearnedCoefficientStore 현재 계수 스냅샷
            seq_plan:       SequencePlan (있으면 seq_plan_snapshot에 저장)
            episode_no:     에피소드 번호

        Returns:
            SLMRecord
        """
        slm = SLMRecord(
            record_id        = str(uuid.uuid4())[:8],
            scene_id         = getattr(scene_record, "scene_id", "unknown"),
            seq_id           = getattr(scene_record, "seq_id", ""),
            episode_no       = episode_no,
            scene_text       = getattr(scene_record, "text", ""),
            consensus        = getattr(scene_record, "consensus", False),
            retries          = getattr(scene_record, "retries", 0),
            mae_score        = getattr(scene_record, "mae_score", 0.0),
            metrics_snapshot = self._extract_metrics(scene_record),
            coeff_snapshot   = coeff_snapshot or {},
            seq_plan_snapshot= seq_plan.to_dict() if seq_plan is not None else {},
            project_id       = self._project_id,
        )
        self._records.append(slm)
        self._append_jsonl(slm)
        return slm

    def collect_from_result(
        self,
        result: Any,                          # E2ESceneGenerationResult
        coeff_snapshot: dict[str, float] | None = None,
    ) -> list[SLMRecord]:
        """
        E2ESceneGenerationResult 전체에서 일괄 수집.

        Args:
            result:         SceneGenerationOrchestrator.run_episode() 반환값
            coeff_snapshot: 에피소드 종료 시점 계수 스냅샷

        Returns:
            List[SLMRecord]
        """
        episode_no = getattr(result, "episode_no", 1)
        collected: list[SLMRecord] = []
        for rec in getattr(result, "scenes", []):
            slm = self.collect(
                scene_record   = rec,
                coeff_snapshot = coeff_snapshot or {},
                episode_no     = episode_no,
            )
            collected.append(slm)
        return collected

    def export_as_slm_dataset(self) -> list[dict[str, Any]]:
        """
        V326 instruction-tuning 포맷으로 내보내기.
        consensus=True인 레코드만 포함.

        Returns:
            List[{record_id, instruction, output, quality}]
        """
        pairs: list[dict[str, Any]] = []
        for rec in self._records:
            pair = rec.as_slm_pair()
            if pair is not None:
                pairs.append(pair)
        return pairs

    def export_jsonl(self, output_path: str | Path | None = None) -> Path:
        """
        전체 레코드를 JSONL 파일로 내보내기.

        Args:
            output_path: None이면 store_path/slm_export.jsonl

        Returns:
            저장된 파일 경로
        """
        path = Path(output_path) if output_path else self._store_path / "slm_export.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for rec in self._records:
                f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        return path

    def statistics(self) -> dict[str, Any]:
        """수집 통계 요약."""
        total    = len(self._records)
        consensus= sum(1 for r in self._records if r.consensus)
        avg_score= (sum(r.mae_score for r in self._records) / total) if total else 0.0
        avg_retry= (sum(r.retries   for r in self._records) / total) if total else 0.0
        return {
            "total_records":     total,
            "consensus_records": consensus,
            "consensus_rate":    round(consensus / total, 4) if total else 0.0,
            "avg_mae_score":     round(avg_score, 4),
            "avg_retries":       round(avg_retry, 4),
            "slm_ready_count":   len(self.export_as_slm_dataset()),
        }

    def clear(self) -> None:
        """메모리 내 레코드 초기화 (JSONL 파일은 유지)."""
        self._records.clear()

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _extract_metrics(self, scene_record: Any) -> dict[str, Any]:
        """SceneRecord의 focus_ctx에서 metrics 추출."""
        ctx = getattr(scene_record, "focus_ctx", {})
        if isinstance(ctx, dict):
            return {
                "temporal_delta":     ctx.get("temporal_delta", 0.0),
                "emotional_pressure": ctx.get("emotional_pressure", 0.0),
            }
        return {}

    def _append_jsonl(self, slm: SLMRecord) -> None:
        """JSONL 파일에 레코드 추가 (append 모드)."""
        try:
            with self._jsonl_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(slm.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass
