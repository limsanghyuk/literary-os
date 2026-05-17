"""
V445: DatasetCardGenerator + TrainingDataRegistry (ADR-008)

DatasetCardGenerator:
  HuggingFace Model Card 표준 포맷으로 데이터셋 메타데이터 카드 생성.
  통계, 라이선스, 편향 분석, 큐레이션 정책 포함.

TrainingDataRegistry (ADR-008):
  버전 관리, 동의 추적, 삭제 요청 처리.
  append-only audit log + 불변 스냅샷.

LLM 0회.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── 공통 유틸 ──────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ═══════════════════════════════════════════════════════════════════════════
# DatasetCardGenerator
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DatasetStats:
    """데이터셋 기본 통계."""
    total_records: int
    canonical_count: int
    candidate_count: int
    archive_count: int
    genre_distribution: dict[str, int]
    style_distribution: dict[str, int]
    avg_L_total: float
    avg_reader_pull: float

    @property
    def canonical_ratio(self) -> float:
        return round(self.canonical_count / max(self.total_records, 1), 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records":      self.total_records,
            "canonical_count":    self.canonical_count,
            "candidate_count":    self.candidate_count,
            "archive_count":      self.archive_count,
            "canonical_ratio":    self.canonical_ratio,
            "genre_distribution": self.genre_distribution,
            "style_distribution": self.style_distribution,
            "avg_L_total":        self.avg_L_total,
            "avg_reader_pull":    self.avg_reader_pull,
        }


@dataclass
class BiasAnalysis:
    """데이터셋 편향 분석 결과."""
    genre_imbalance_ratio: float        # max_genre_count / min_genre_count
    dominant_genre: str
    dominant_genre_ratio: float
    style_imbalance_ratio: float
    pii_scrubbed_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "genre_imbalance_ratio":  self.genre_imbalance_ratio,
            "dominant_genre":         self.dominant_genre,
            "dominant_genre_ratio":   self.dominant_genre_ratio,
            "style_imbalance_ratio":  self.style_imbalance_ratio,
            "pii_scrubbed_count":     self.pii_scrubbed_count,
            "warnings":               self.warnings,
        }


class DatasetCardGenerator:
    """
    HuggingFace 표준 데이터셋 카드 생성기.

    생성 포맷:
      - YAML frontmatter (tags, license, language)
      - Markdown 본문 (description, stats, curation, bias, license)
      - JSON 상세 리포트 (bias_analysis + stats)
    """

    SUPPORTED_LICENSES = {"cc-by-4.0", "cc-by-nc-4.0", "apache-2.0", "mit", "proprietary"}
    DEFAULT_LANGUAGE = ["ko"]
    DEFAULT_TAGS = ["literary", "creative-writing", "korean", "drama", "slm-training"]

    def __init__(
        self,
        dataset_name: str,
        version: str,
        license_id: str = "cc-by-nc-4.0",
        language: list[str] | None = None,
        extra_tags: list[str] | None = None,
    ):
        if license_id not in self.SUPPORTED_LICENSES:
            raise ValueError(
                f"지원하지 않는 라이선스: {license_id}. "
                f"지원 목록: {sorted(self.SUPPORTED_LICENSES)}"
            )
        self.dataset_name = dataset_name
        self.version      = version
        self.license_id   = license_id
        self.language     = language or self.DEFAULT_LANGUAGE
        self.tags         = list(self.DEFAULT_TAGS) + (extra_tags or [])

    # ── 공개 메서드 ─────────────────────────────────────────────────────

    def compute_stats(self, records: list) -> DatasetStats:
        """TraceRecord 목록 → DatasetStats."""
        from literary_system.trace.trace_dataset_store import PromotionTier
        total    = len(records)
        canon    = sum(1 for r in records if r.promotion == PromotionTier.CANONICAL)
        cand     = sum(1 for r in records if r.promotion == PromotionTier.CANDIDATE)
        archive  = sum(1 for r in records if r.promotion == PromotionTier.ARCHIVE)

        genre_dist: dict[str, int] = {}
        style_dist: dict[str, int] = {}
        for r in records:
            g = r.seed_contract.get("genre", "unknown")
            genre_dist[g] = genre_dist.get(g, 0) + 1
            s = str(r.style_dna_profile)
            style_dist[s] = style_dist.get(s, 0) + 1

        l_totals = [r.loss_report.get("L_total", 1.0) for r in records]
        pulls    = [r.reader_estimate.get("reader_pull", 0.0) for r in records]

        return DatasetStats(
            total_records=total,
            canonical_count=canon,
            candidate_count=cand,
            archive_count=archive,
            genre_distribution=genre_dist,
            style_distribution=style_dist,
            avg_L_total=round(sum(l_totals) / max(total, 1), 4),
            avg_reader_pull=round(sum(pulls) / max(total, 1), 4),
        )

    def analyze_bias(self, stats: DatasetStats, pii_scrubbed: int = 0) -> BiasAnalysis:
        """DatasetStats → BiasAnalysis."""
        warnings: list[str] = []

        # 장르 불균형
        genre_counts = list(stats.genre_distribution.values()) or [1]
        max_g, min_g = max(genre_counts), max(min(genre_counts), 1)
        genre_ratio  = round(max_g / min_g, 2)
        dominant     = max(stats.genre_distribution, key=stats.genre_distribution.get, default="unknown")
        dom_ratio    = round(stats.genre_distribution.get(dominant, 0) / max(stats.total_records, 1), 4)

        if genre_ratio > 5.0:
            warnings.append(
                f"장르 불균형 심각: {dominant} 비율 {dom_ratio:.1%} "
                f"(불균형 비율 {genre_ratio}x)"
            )

        # 스타일 불균형
        style_counts = list(stats.style_distribution.values()) or [1]
        max_s, min_s = max(style_counts), max(min(style_counts), 1)
        style_ratio  = round(max_s / min_s, 2)
        if style_ratio > 10.0:
            warnings.append(f"스타일 불균형 심각: {style_ratio}x")

        # canonical 비율 경고
        if stats.canonical_ratio < 0.3:
            warnings.append(
                f"CANONICAL 비율 낮음: {stats.canonical_ratio:.1%} (권장 ≥ 30%)"
            )

        return BiasAnalysis(
            genre_imbalance_ratio=genre_ratio,
            dominant_genre=dominant,
            dominant_genre_ratio=dom_ratio,
            style_imbalance_ratio=style_ratio,
            pii_scrubbed_count=pii_scrubbed,
            warnings=warnings,
        )

    def generate_card(
        self,
        records: list,
        out_path: str | Path | None = None,
        pii_scrubbed: int = 0,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        데이터셋 카드 생성 (Markdown + YAML frontmatter).

        Returns dict with: card_text (str), stats, bias_analysis, out_path.
        """
        stats = self.compute_stats(records)
        bias  = self.analyze_bias(stats, pii_scrubbed)

        card_text = self._render_markdown(stats, bias, description)

        result: dict[str, Any] = {
            "card_text":     card_text,
            "stats":         stats.to_dict(),
            "bias_analysis": bias.to_dict(),
            "dataset_name":  self.dataset_name,
            "version":       self.version,
            "license":       self.license_id,
            "generated_at":  _now_iso(),
        }

        if out_path:
            out = Path(out_path)
            out.write_text(card_text, encoding="utf-8")
            result["out_path"] = str(out)

        return result

    # ── 내부 렌더링 ──────────────────────────────────────────────────────

    def _render_markdown(
        self, stats: DatasetStats, bias: BiasAnalysis, description: str | None
    ) -> str:
        tags_str = "\n".join(f"  - {t}" for t in self.tags)
        lang_str = "\n".join(f"  - {l}" for l in self.language)

        desc = description or (
            f"{self.dataset_name}은 Literary OS 파이프라인이 생성한 "
            "한국어 문학 창작 학습 데이터셋입니다."
        )

        genre_rows = "\n".join(
            f"| {g} | {c} | {c/max(stats.total_records,1):.1%} |"
            for g, c in sorted(stats.genre_distribution.items(), key=lambda x: -x[1])
        )

        bias_warnings = (
            "\n".join(f"- ⚠️ {w}" for w in bias.warnings)
            if bias.warnings
            else "- ✅ 심각한 편향 없음"
        )

        return f"""---
dataset_info:
  name: {self.dataset_name}
  version: {self.version}
  license: {self.license_id}
language:
{lang_str}
tags:
{tags_str}
---

# {self.dataset_name}

## 데이터셋 설명

{desc}

## 통계

| 지표 | 값 |
|------|-----|
| 전체 레코드 | {stats.total_records} |
| CANONICAL | {stats.canonical_count} ({stats.canonical_ratio:.1%}) |
| CANDIDATE | {stats.candidate_count} |
| 평균 L_total | {stats.avg_L_total:.4f} |
| 평균 reader_pull | {stats.avg_reader_pull:.4f} |
| PII 마스킹 | {bias.pii_scrubbed_count} |

## 장르 분포

| 장르 | 수 | 비율 |
|------|-----|------|
{genre_rows}

## 편향 분석

{bias_warnings}

## 큐레이션 정책

- PromotionTier CANONICAL/CANDIDATE만 포함 (ARCHIVE 제외)
- MinHash Jaccard ≥ 0.85 중복 제거
- PII 정규식 마스킹 (전화·이메일·주민번호·카드번호·주소·이름)
- Stratified split: train 80% / val 10% / test 10%

## 라이선스

{self.license_id}
"""


# ═══════════════════════════════════════════════════════════════════════════
# TrainingDataRegistry (ADR-008)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DatasetVersion:
    """데이터셋 버전 스냅샷 (불변)."""
    version_id:    str           # UUID4
    version_tag:   str           # e.g. "v1.0.0"
    dataset_name:  str
    record_ids:    tuple[str, ...]
    stats_summary: dict[str, Any]
    created_at:    str
    creator:       str
    notes:         str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id":    self.version_id,
            "version_tag":   self.version_tag,
            "dataset_name":  self.dataset_name,
            "record_ids":    list(self.record_ids),
            "stats_summary": self.stats_summary,
            "created_at":    self.created_at,
            "creator":       self.creator,
            "notes":         self.notes,
        }


@dataclass(frozen=True)
class ConsentRecord:
    """데이터 사용 동의 기록."""
    consent_id:  str
    subject_id:  str
    dataset:     str
    granted:     bool
    timestamp:   str
    purpose:     str   # "slm_training" | "evaluation" | "augmentation"
    expires_at:  str | None = None   # None = 영구

    def to_dict(self) -> dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "subject_id": self.subject_id,
            "dataset":    self.dataset,
            "granted":    self.granted,
            "timestamp":  self.timestamp,
            "purpose":    self.purpose,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True)
class DeletionRequest:
    """삭제 요청 기록 (ADR-008 §3)."""
    request_id:  str
    subject_id:  str
    dataset:     str
    record_ids:  tuple[str, ...]
    requested_at: str
    status:      str   # "pending" | "completed" | "rejected"
    reason:      str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id":   self.request_id,
            "subject_id":   self.subject_id,
            "dataset":      self.dataset,
            "record_ids":   list(self.record_ids),
            "requested_at": self.requested_at,
            "status":       self.status,
            "reason":       self.reason,
        }


class TrainingDataRegistry:
    """
    ADR-008 준수 학습 데이터 레지스트리.

    - 버전 관리: register_version()
    - 동의 추적: record_consent() / revoke_consent()
    - 삭제 요청: request_deletion() / complete_deletion()
    - 감사 로그: audit_log (append-only)
    """

    def __init__(self, registry_root: str | Path | None = None):
        self._versions:  dict[str, DatasetVersion] = {}     # version_id → DatasetVersion
        self._consents:  dict[str, ConsentRecord]  = {}     # consent_id → ConsentRecord
        self._deletions: dict[str, DeletionRequest] = {}    # request_id → DeletionRequest
        self._audit_log: list[dict[str, Any]]       = []    # append-only

        if registry_root:
            self._root = Path(registry_root)
            self._root.mkdir(parents=True, exist_ok=True)
        else:
            self._root = None

    # ── 버전 관리 ──────────────────────────────────────────────────────

    def register_version(
        self,
        version_tag: str,
        dataset_name: str,
        record_ids: list[str],
        stats_summary: dict[str, Any],
        creator: str = "literary_os",
        notes: str = "",
    ) -> DatasetVersion:
        """새 데이터셋 버전을 등록하고 불변 스냅샷을 반환."""
        version_id = str(uuid.uuid4())
        version = DatasetVersion(
            version_id=version_id,
            version_tag=version_tag,
            dataset_name=dataset_name,
            record_ids=tuple(record_ids),
            stats_summary=stats_summary,
            created_at=_now_iso(),
            creator=creator,
            notes=notes,
        )
        self._versions[version_id] = version
        self._append_audit("register_version", {
            "version_id":  version_id,
            "version_tag": version_tag,
            "record_count": len(record_ids),
        })
        if self._root:
            self._persist_version(version)
        return version

    def get_version(self, version_id: str) -> DatasetVersion | None:
        return self._versions.get(version_id)

    def list_versions(self, dataset_name: str | None = None) -> list[DatasetVersion]:
        vs = list(self._versions.values())
        if dataset_name:
            vs = [v for v in vs if v.dataset_name == dataset_name]
        return sorted(vs, key=lambda v: v.created_at)

    # ── 동의 추적 ─────────────────────────────────────────────────────

    def record_consent(
        self,
        subject_id: str,
        dataset: str,
        purpose: str = "slm_training",
        expires_at: str | None = None,
    ) -> ConsentRecord:
        consent = ConsentRecord(
            consent_id=str(uuid.uuid4()),
            subject_id=subject_id,
            dataset=dataset,
            granted=True,
            timestamp=_now_iso(),
            purpose=purpose,
            expires_at=expires_at,
        )
        self._consents[consent.consent_id] = consent
        self._append_audit("record_consent", {
            "subject_id": subject_id,
            "dataset":    dataset,
            "purpose":    purpose,
        })
        return consent

    def revoke_consent(self, consent_id: str) -> bool:
        """동의 철회 — 레코드를 REVOKED 상태로 교체."""
        if consent_id not in self._consents:
            return False
        old = self._consents[consent_id]
        # frozen dataclass → 새 객체 생성
        import dataclasses
        revoked = dataclasses.replace(old, granted=False)
        self._consents[consent_id] = revoked
        self._append_audit("revoke_consent", {
            "consent_id": consent_id,
            "subject_id": old.subject_id,
        })
        return True

    def has_consent(self, subject_id: str, dataset: str, purpose: str = "slm_training") -> bool:
        return any(
            c.subject_id == subject_id
            and c.dataset == dataset
            and c.purpose == purpose
            and c.granted
            for c in self._consents.values()
        )

    # ── 삭제 요청 ─────────────────────────────────────────────────────

    def request_deletion(
        self,
        subject_id: str,
        dataset: str,
        record_ids: list[str],
        reason: str = "user_request",
    ) -> DeletionRequest:
        req = DeletionRequest(
            request_id=str(uuid.uuid4()),
            subject_id=subject_id,
            dataset=dataset,
            record_ids=tuple(record_ids),
            requested_at=_now_iso(),
            status="pending",
            reason=reason,
        )
        self._deletions[req.request_id] = req
        self._append_audit("request_deletion", {
            "subject_id": subject_id,
            "record_count": len(record_ids),
        })
        return req

    def complete_deletion(self, request_id: str) -> bool:
        """삭제 완료 처리."""
        if request_id not in self._deletions:
            return False
        import dataclasses
        old = self._deletions[request_id]
        done = dataclasses.replace(old, status="completed")
        self._deletions[request_id] = done
        self._append_audit("complete_deletion", {
            "request_id": request_id,
            "subject_id": old.subject_id,
        })
        return True

    def pending_deletions(self) -> list[DeletionRequest]:
        return [r for r in self._deletions.values() if r.status == "pending"]

    # ── 감사 로그 ─────────────────────────────────────────────────────

    def audit_log(self) -> list[dict[str, Any]]:
        """전체 감사 로그 반환 (불변 복사본)."""
        return list(self._audit_log)

    def export(self, out_path: str | Path) -> dict[str, Any]:
        """전체 레지스트리를 JSON으로 내보내기."""
        data = {
            "exported_at": _now_iso(),
            "versions":    [v.to_dict() for v in self._versions.values()],
            "consents":    [c.to_dict() for c in self._consents.values()],
            "deletions":   [d.to_dict() for d in self._deletions.values()],
            "audit_log":   list(self._audit_log),
        }
        Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"exported_to": str(out_path), "entry_counts": {
            "versions":  len(self._versions),
            "consents":  len(self._consents),
            "deletions": len(self._deletions),
            "audit_entries": len(self._audit_log),
        }}

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────

    def _append_audit(self, action: str, detail: dict[str, Any]) -> None:
        self._audit_log.append({
            "action":    action,
            "timestamp": _now_iso(),
            "detail":    detail,
        })

    def _persist_version(self, v: DatasetVersion) -> None:
        if self._root:
            p = self._root / f"{v.version_id}.json"
            p.write_text(json.dumps(v.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
