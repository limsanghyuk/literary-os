"""
V316: TraceDatasetStore
Canonical 성공 씬의 Trace를 누적하여 SLM 학습 재료를 구성.

핵심 철학:
  파라미터 재학습 없이 제도적 학습.
  "좋은 씬이 왜 좋았는가"를 데이터로 남긴다.

누적 구조:
  canonical_fewshot  → 최고 품질 학습 예시
  candidate_fewshot  → 잠재적 예시
  repair_log         → 무엇이 고쳐졌는가
  critic_log         → 무엇이 잡혔는가
  trajectory_log     → Literary State 궤도 이력

이것이 충분히 쌓이면:
  {"input": 패킷 전체, "output": 최종 산문}
  의 쌍이 SLM instruction-tuning 데이터가 된다.

LLM 0회.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── 승격 등급 ──────────────────────────────────────────────
class PromotionTier:
    CANONICAL  = "canonical_fewshot"   # L_total ≤ 0.12
    CANDIDATE  = "candidate_fewshot"   # L_total ≤ 0.20
    ARCHIVE    = "archive_only"        # 그 외
    REPAIR_LOG = "repair_log"          # 수리 기록
    CRITIC_LOG = "critic_log"          # 비평 기록


@dataclass
class TraceRecord:
    """
    단일 씬 생성 전체의 추적 기록.
    SLM 학습 데이터의 원자 단위.
    """
    trace_id: str
    project_id: str
    episode_no: int
    scene_id: str
    created_at: str

    # ── 입력 패킷 (학습 입력) ─────────────────────────────
    seed_contract: dict[str, Any]
    style_dna_profile: str  # [갭 2 수정] commit()에서 dict를 str로 자동 변환하여 저장
    macroarc_intent: str
    literary_state_before: dict[str, float]
    fewshot_refs_used: list[str]

    # ── 생성 결과 (학습 출력) ─────────────────────────────
    render_output: dict[str, str]          # {"SC01": "...", "SC02": "..."}
    literary_state_after: dict[str, float]
    literary_state_delta: dict[str, float]

    # ── 품질 지표 ─────────────────────────────────────────
    loss_report: dict[str, float]          # L_total, L_struct, ...
    reader_estimate: dict[str, float]      # reader_pull, afterimage, ai_smell
    trajectory_deviation: float            # 목표 궤도 이탈 거리
    critic_findings_count: int
    repair_applied: bool
    hitl_recommended: bool

    # ── 승격 ─────────────────────────────────────────────
    promotion: str                         # PromotionTier.*
    promotion_reason: str

    # ── 메타 ─────────────────────────────────────────────
    call_count: int = 1
    knowledge_pressure: float = 0.0       # 해당 씬의 지식 비대칭 압력

    def as_slm_pair(self) -> dict[str, Any] | None:
        """
        SLM instruction-tuning용 (input, output) 쌍.
        canonical 또는 candidate만 학습 데이터로 변환.
        """
        if self.promotion == PromotionTier.ARCHIVE:
            return None

        instruction = (
            f"[Genre] {self.seed_contract.get('genre', 'drama')}\n"
            f"[Style] {self.style_dna_profile}\n"
            f"[Intent] {self.macroarc_intent}\n"
            f"[State] SP={self.literary_state_before.get('SP', 0):.2f} "
            f"RU={self.literary_state_before.get('RU', 0):.2f} "
            f"ET={self.literary_state_before.get('ET', 0):.2f}\n"
            f"[Seed] {self.seed_contract.get('user_prompt', '')}"
        )

        output_text = "\n\n".join(
            f"[{scene_id}]\n{text}"
            for scene_id, text in self.render_output.items()
            if text.strip()
        )

        if not output_text.strip():
            return None

        return {
            "trace_id":    self.trace_id,
            "promotion":   self.promotion,
            "instruction": instruction,
            "output":      output_text,
            "quality": {
                "L_total":      self.loss_report.get("L_total", 1.0),
                "reader_pull":  self.reader_estimate.get("reader_pull", 0.0),
                "ai_smell":     self.reader_estimate.get("ai_smell_score", 1.0),
                "deviation":    self.trajectory_deviation,
            },
        }


class TraceDatasetStore:
    """
    Trace 기록 누적 + SLM 학습 데이터 추출 엔진.
    파일 기반 (JSON Lines) — ChromaDB 없이도 동작.
    """

    def __init__(self, store_root: str | Path = "./data/traces"):
        self.root = Path(store_root)
        self.root.mkdir(parents=True, exist_ok=True)

        self._canonical_file  = self.root / "canonical_fewshot.jsonl"
        self._candidate_file  = self.root / "candidate_fewshot.jsonl"
        self._repair_file     = self.root / "repair_log.jsonl"
        self._critic_file     = self.root / "critic_log.jsonl"
        self._all_file        = self.root / "all_traces.jsonl"

        # 인메모리 인덱스 (빠른 조회)
        self._index: dict[str, TraceRecord] = {}
        self._by_genre: dict[str, list[str]] = {}       # genre → [trace_id]
        self._by_profile: dict[str, list[str]] = {}     # style_profile → [trace_id]

    # ── 저장 ──────────────────────────────────────────────
    def commit(self, record: TraceRecord) -> dict[str, Any]:
        """Trace 기록을 저장하고 적절한 버킷에 분류."""
        record_dict = self._to_dict(record)

        # 전체 로그
        self._append(self._all_file, record_dict)

        # 버킷별 분류
        if record.promotion == PromotionTier.CANONICAL:
            self._append(self._canonical_file, record_dict)
        elif record.promotion == PromotionTier.CANDIDATE:
            self._append(self._candidate_file, record_dict)

        # 인메모리 인덱스
        self._index[record.trace_id] = record
        genre = record.seed_contract.get("genre", "unknown")
        self._by_genre.setdefault(genre, []).append(record.trace_id)
        # [갭 2 수정] style_dna_profile이 dict이면 str로 변환 (unhashable 방지)
        profile_key = (
            str(sorted(record.style_dna_profile.items()))
            if isinstance(record.style_dna_profile, dict)
            else str(record.style_dna_profile)
        )
        self._by_profile.setdefault(profile_key, []).append(record.trace_id)

        return {
            "trace_id":  record.trace_id,
            "promotion": record.promotion,
            "L_total":   record.loss_report.get("L_total", 1.0),
            "stored_to": str(
                self._canonical_file if record.promotion == PromotionTier.CANONICAL
                else self._candidate_file if record.promotion == PromotionTier.CANDIDATE
                else self._all_file
            ),
        }

    def commit_repair_log(
        self,
        trace_id: str,
        repair_targets: list[str],
        before_text: str,
        after_text: str,
        critic_pattern: str,
        L_before: float,
        L_after: float,
    ) -> None:
        """수리 기록 저장 — "무엇이 어떻게 고쳐졌는가"."""
        record = {
            "log_id":        f"repair_{uuid.uuid4().hex[:8]}",
            "trace_id":      trace_id,
            "created_at":    _now(),
            "repair_targets": repair_targets,
            "critic_pattern": critic_pattern,
            "before_text":   before_text[:500],
            "after_text":    after_text[:500],
            "L_before":      L_before,
            "L_after":       L_after,
            "improvement":   round(L_before - L_after, 4),
        }
        self._append(self._repair_file, record)

    def commit_critic_log(
        self,
        trace_id: str,
        findings: list[dict],
        overall_decision: str,
    ) -> None:
        """비평 기록 저장 — "무엇이 잡혔는가"."""
        record = {
            "log_id":           f"critic_{uuid.uuid4().hex[:8]}",
            "trace_id":         trace_id,
            "created_at":       _now(),
            "findings_count":   len(findings),
            "findings_summary": [
                {"pattern": f.get("pattern", ""), "priority": f.get("priority", 0)}
                for f in findings[:5]
            ],
            "overall_decision": overall_decision,
        }
        self._append(self._critic_file, record)

    # ── 조회 ──────────────────────────────────────────────
    def get(self, trace_id: str) -> TraceRecord | None:
        return self._index.get(trace_id)

    def search_by_genre(self, genre: str, tier: str | None = None) -> list[TraceRecord]:
        ids = self._by_genre.get(genre, [])
        records = [self._index[i] for i in ids if i in self._index]
        if tier:
            records = [r for r in records if r.promotion == tier]
        return sorted(records, key=lambda r: r.loss_report.get("L_total", 1.0))

    def search_by_profile(self, profile: str) -> list[TraceRecord]:
        ids = self._by_profile.get(profile, [])
        return [self._index[i] for i in ids if i in self._index]

    def best_canonical(self, genre: str, n: int = 3) -> list[TraceRecord]:
        """해당 장르의 최고 canonical 기록 n개."""
        records = self.search_by_genre(genre, tier=PromotionTier.CANONICAL)
        return records[:n]

    # ── SLM 학습 데이터 추출 ─────────────────────────────
    def export_slm_dataset(
        self,
        out_path: str | Path | None = None,
        min_tier: str = PromotionTier.CANDIDATE,
        max_L_total: float = 0.20,
    ) -> dict[str, Any]:
        """
        누적된 Trace에서 SLM 학습 데이터셋 추출.
        출력: instruction-tuning용 JSONL
        """
        out_path = Path(out_path or self.root / "slm_dataset.jsonl")
        pairs = []
        skipped = 0

        for record in self._index.values():
            if record.loss_report.get("L_total", 1.0) > max_L_total:
                skipped += 1
                continue
            if record.promotion == PromotionTier.ARCHIVE:
                skipped += 1
                continue
            pair = record.as_slm_pair()
            if pair:
                pairs.append(pair)

        # 품질 순 정렬
        pairs.sort(key=lambda x: x["quality"]["L_total"])

        with open(out_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

        return {
            "exported":    len(pairs),
            "skipped":     skipped,
            "output_path": str(out_path),
            "canonical_count": sum(1 for p in pairs if p["promotion"] == PromotionTier.CANONICAL),
            "candidate_count": sum(1 for p in pairs if p["promotion"] == PromotionTier.CANDIDATE),
        }

    def statistics(self) -> dict[str, Any]:
        """누적 현황 요약."""
        total = len(self._index)
        by_tier = {}
        for r in self._index.values():
            by_tier[r.promotion] = by_tier.get(r.promotion, 0) + 1

        l_totals = [r.loss_report.get("L_total", 1.0) for r in self._index.values()]
        avg_L = round(sum(l_totals) / max(len(l_totals), 1), 4)

        return {
            "total_traces":    total,
            "by_tier":         by_tier,
            "avg_L_total":     avg_L,
            "genres_covered":  list(self._by_genre.keys()),
            "profiles_covered": list(self._by_profile.keys()),
            # [갭 2 수정] CANONICAL + CANDIDATE 모두 SLM 적격으로 집계
            "slm_ready_count": (
                by_tier.get(PromotionTier.CANONICAL, 0)    # 최우수 학습 데이터
                + by_tier.get(PromotionTier.CANDIDATE, 0)  # 후보 학습 데이터
            ),
        }

    # ── 내부 헬퍼 ─────────────────────────────────────────
    def _append(self, path: Path, record: dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _to_dict(self, r: TraceRecord) -> dict:
        return {
            "trace_id":              r.trace_id,
            "project_id":            r.project_id,
            "episode_no":            r.episode_no,
            "scene_id":              r.scene_id,
            "created_at":            r.created_at,
            "seed_contract":         r.seed_contract,
            "style_dna_profile":     r.style_dna_profile,
            "macroarc_intent":       r.macroarc_intent,
            "literary_state_before": r.literary_state_before,
            "literary_state_after":  r.literary_state_after,
            "literary_state_delta":  r.literary_state_delta,
            "fewshot_refs_used":     r.fewshot_refs_used,
            "render_output":         r.render_output,
            "loss_report":           r.loss_report,
            "reader_estimate":       r.reader_estimate,
            "trajectory_deviation":  r.trajectory_deviation,
            "critic_findings_count": r.critic_findings_count,
            "repair_applied":        r.repair_applied,
            "hitl_recommended":      r.hitl_recommended,
            "promotion":             r.promotion,
            "promotion_reason":      r.promotion_reason,
            "call_count":            r.call_count,
            "knowledge_pressure":    r.knowledge_pressure,
        }


def make_trace_record(
    project_id: str,
    episode_no: int,
    scene_id: str,
    seed_contract: dict,
    style_dna_profile: str,  # [갭 2 수정] dict는 commit()에서 str로 자동 변환
    macroarc_intent: str,
    literary_state_before: dict,
    literary_state_after: dict,
    render_output: dict,
    loss_report: dict,
    reader_estimate: dict,
    trajectory_deviation: float,
    critic_findings: list,
    repair_applied: bool,
    hitl_recommended: bool,
    fewshot_refs: list | None = None,
    knowledge_pressure: float = 0.0,
    call_count: int = 1,
) -> TraceRecord:
    """TraceRecord 생성 팩토리."""
    L_total = loss_report.get("L_total", 1.0)

    # 승격 결정
    if L_total <= 0.12 and not repair_applied and call_count <= 2:
        promotion = PromotionTier.CANONICAL
        reason    = f"L_total={L_total:.3f} ≤ 0.12, no_repair, calls≤2"
    elif L_total <= 0.20:
        promotion = PromotionTier.CANDIDATE
        reason    = f"L_total={L_total:.3f} ≤ 0.20"
    else:
        promotion = PromotionTier.ARCHIVE
        reason    = f"L_total={L_total:.3f} > 0.20"

    # state_delta 계산
    delta = {
        k: round(literary_state_after.get(k, 0) - literary_state_before.get(k, 0), 4)
        for k in ["SP", "RU", "ET", "RD", "RT", "AC", "RO", "MR"]
    }

    return TraceRecord(
        trace_id=f"tr_{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        episode_no=episode_no,
        scene_id=scene_id,
        created_at=_now(),
        seed_contract=seed_contract,
        # [갭 2 수정] dict 타입 방어: unhashable type 방지
        style_dna_profile=(
            str(sorted(style_dna_profile.items()))
            if isinstance(style_dna_profile, dict)
            else str(style_dna_profile)
        ),
        macroarc_intent=macroarc_intent,
        literary_state_before=literary_state_before,
        literary_state_after=literary_state_after,
        literary_state_delta=delta,
        fewshot_refs_used=fewshot_refs or [],
        render_output=render_output,
        loss_report=loss_report,
        reader_estimate=reader_estimate,
        trajectory_deviation=trajectory_deviation,
        critic_findings_count=len(critic_findings),
        repair_applied=repair_applied,
        hitl_recommended=hitl_recommended,
        promotion=promotion,
        promotion_reason=reason,
        call_count=call_count,
        knowledge_pressure=knowledge_pressure,
    )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
