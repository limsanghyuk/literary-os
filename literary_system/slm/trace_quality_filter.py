"""
V444: TraceQualityFilter
PromotionTier 필터 + MinHash 중복 제거 + Stratified split

핵심 역할:
  TraceDatasetStore의 레코드를 학습 데이터셋으로 정제한다.
  1) PromotionTier 허용 목록으로 1차 필터
  2) MinHash Jaccard similarity로 중복 제거
  3) 장르 × 티어 계층화 후 train/val/test 분할

순수 Python — 외부 의존 0.
"""
from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from literary_system.trace.trace_dataset_store import TraceRecord, PromotionTier

# ── MinHash ───────────────────────────────────────────────────────────────

NUM_HASHES: int = 128   # MinHash 서명 길이 (정밀도↑ vs 속도↓)
SHINGLE_K:  int = 3     # k-shingle 크기 (문자 단위)


def _shingles(text: str, k: int = SHINGLE_K) -> set[str]:
    """텍스트 → k-문자 shingle 집합."""
    text = text.lower()
    if len(text) < k:
        return {text} if text else set()
    return {text[i:i + k] for i in range(len(text) - k + 1)}


def _token_hash(token: str, seed: int) -> int:
    """seed-based deterministic hash (no external deps)."""
    raw = f"{seed}:{token}".encode("utf-8")
    return int(hashlib.md5(raw).hexdigest(), 16)


def minhash_signature(text: str, num_hashes: int = NUM_HASHES) -> list[int]:
    """텍스트 → MinHash 서명 (길이 num_hashes의 정수 리스트)."""
    shingle_set = _shingles(text)
    if not shingle_set:
        return [0] * num_hashes
    return [
        min(_token_hash(s, seed) for s in shingle_set)
        for seed in range(num_hashes)
    ]


def jaccard_estimate(sig_a: list[int], sig_b: list[int]) -> float:
    """두 MinHash 서명으로 Jaccard 유사도를 추정."""
    if len(sig_a) != len(sig_b) or not sig_a:
        return 0.0
    matches = sum(a == b for a, b in zip(sig_a, sig_b))
    return matches / len(sig_a)


# ── Dataclasses ───────────────────────────────────────────────────────────

@dataclass
class DedupStats:
    """중복 제거 통계."""
    original_count:  int
    removed_count:   int
    kept_count:      int
    threshold:       float
    duplicate_pairs: list[tuple[str, str]] = field(default_factory=list)

    @property
    def removal_rate(self) -> float:
        return round(self.removed_count / max(self.original_count, 1), 4)

    def summary(self) -> str:
        return (
            f"dedup: {self.original_count} → {self.kept_count} "
            f"(removed {self.removed_count}, rate={self.removal_rate:.1%}, "
            f"threshold={self.threshold})"
        )


@dataclass
class SplitResult:
    """Stratified split 결과."""
    train:      list[TraceRecord]
    val:        list[TraceRecord]
    test:       list[TraceRecord]
    train_ratio: float
    val_ratio:   float
    test_ratio:  float

    @property
    def counts(self) -> dict[str, int]:
        return {"train": len(self.train), "val": len(self.val), "test": len(self.test)}

    @property
    def total(self) -> int:
        return len(self.train) + len(self.val) + len(self.test)

    def summary(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "counts": self.counts,
            "ratios": {
                "train": round(len(self.train) / max(self.total, 1), 3),
                "val":   round(len(self.val)   / max(self.total, 1), 3),
                "test":  round(len(self.test)  / max(self.total, 1), 3),
            },
        }


@dataclass
class FilterResult:
    """run() 전체 파이프라인 결과."""
    split:          SplitResult
    dedup_stats:    DedupStats
    tier_filtered:  int          # tier 필터로 제거된 수
    pii_scrubbed:   int          # PII 마스킹된 레코드 수 (scrub 활성 시)
    allowed_tiers:  list[str]
    config:         dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "tier_filtered":  self.tier_filtered,
            "dedup":          self.dedup_stats.summary(),
            "pii_scrubbed":   self.pii_scrubbed,
            "split":          self.split.summary(),
            "allowed_tiers":  self.allowed_tiers,
        }


# ── TraceQualityFilter ────────────────────────────────────────────────────

class TraceQualityFilter:
    """
    TraceRecord 목록 → 정제된 train/val/test split.

    파이프라인:
      1. filter_by_tier()   — PromotionTier 화이트리스트
      2. deduplicate()      — MinHash Jaccard 중복 제거
      3. stratified_split() — 장르 × tier 계층 분할
    """

    DEFAULT_ALLOWED_TIERS = [PromotionTier.CANONICAL, PromotionTier.CANDIDATE]
    DEFAULT_DEDUP_THRESHOLD = 0.85   # Jaccard ≥ 0.85 → 중복
    DEFAULT_TRAIN_RATIO = 0.80
    DEFAULT_VAL_RATIO   = 0.10
    DEFAULT_TEST_RATIO  = 0.10

    def __init__(
        self,
        allowed_tiers:    list[str] | None = None,
        dedup_threshold:  float = DEFAULT_DEDUP_THRESHOLD,
        train_ratio:      float = DEFAULT_TRAIN_RATIO,
        val_ratio:        float = DEFAULT_VAL_RATIO,
        test_ratio:       float = DEFAULT_TEST_RATIO,
        random_seed:      int   = 42,
        scrub_pii:        bool  = False,
    ):
        self.allowed_tiers   = allowed_tiers or list(self.DEFAULT_ALLOWED_TIERS)
        self.dedup_threshold = dedup_threshold
        self.train_ratio     = train_ratio
        self.val_ratio       = val_ratio
        self.test_ratio      = test_ratio
        self.random_seed     = random_seed
        self.scrub_pii       = scrub_pii

        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
            raise ValueError(
                f"비율 합이 1.0이어야 합니다: "
                f"{train_ratio}+{val_ratio}+{test_ratio}="
                f"{train_ratio+val_ratio+test_ratio}"
            )

    # ── 공개 메서드 ───────────────────────────────────────────────────

    def filter_by_tier(self, records: list[TraceRecord]) -> tuple[list[TraceRecord], int]:
        """
        허용된 PromotionTier 레코드만 통과.
        Returns (filtered_records, removed_count).
        """
        kept = [r for r in records if r.promotion in self.allowed_tiers]
        removed = len(records) - len(kept)
        return kept, removed

    def deduplicate(
        self,
        records: list[TraceRecord],
        threshold: float | None = None,
    ) -> tuple[list[TraceRecord], DedupStats]:
        """
        MinHash Jaccard 유사도 기반 중복 제거.
        유사도 ≥ threshold인 쌍 중 나중 것을 제거.
        Returns (unique_records, DedupStats).
        """
        thr = threshold if threshold is not None else self.dedup_threshold
        original = len(records)

        # 각 레코드의 텍스트 콘텐츠를 MinHash로 서명
        sigs: list[list[int]] = []
        for r in records:
            text = " ".join(r.render_output.values())
            sigs.append(minhash_signature(text))

        removed_indices: set[int] = set()
        duplicate_pairs: list[tuple[str, str]] = []

        for i in range(len(records)):
            if i in removed_indices:
                continue
            for j in range(i + 1, len(records)):
                if j in removed_indices:
                    continue
                sim = jaccard_estimate(sigs[i], sigs[j])
                if sim >= thr:
                    removed_indices.add(j)
                    duplicate_pairs.append((records[i].trace_id, records[j].trace_id))

        unique = [r for idx, r in enumerate(records) if idx not in removed_indices]
        stats = DedupStats(
            original_count=original,
            removed_count=len(removed_indices),
            kept_count=len(unique),
            threshold=thr,
            duplicate_pairs=duplicate_pairs,
        )
        return unique, stats

    def stratified_split(
        self,
        records: list[TraceRecord],
        train_ratio: float | None = None,
        val_ratio:   float | None = None,
        test_ratio:  float | None = None,
    ) -> SplitResult:
        """
        장르 × PromotionTier 계층화 후 train/val/test 분할.
        각 계층에서 독립적으로 비율을 적용해 편향을 최소화.
        """
        tr = train_ratio if train_ratio is not None else self.train_ratio
        vr = val_ratio   if val_ratio   is not None else self.val_ratio
        te = test_ratio  if test_ratio  is not None else self.test_ratio

        rng = random.Random(self.random_seed)

        # 계층화: (genre, tier) → 레코드 목록
        strata: dict[tuple[str, str], list[TraceRecord]] = defaultdict(list)
        for r in records:
            genre = r.seed_contract.get("genre", "unknown")
            tier  = str(r.promotion)
            strata[(genre, tier)].append(r)

        train_list: list[TraceRecord] = []
        val_list:   list[TraceRecord] = []
        test_list:  list[TraceRecord] = []

        for stratum_records in strata.values():
            shuffled = list(stratum_records)
            rng.shuffle(shuffled)
            n = len(shuffled)

            # 최소 1개 확보 로직: 각 분할에 최소 1개 보장 (n ≥ 3일 때)
            if n == 0:
                continue
            elif n == 1:
                train_list.extend(shuffled)
            elif n == 2:
                train_list.append(shuffled[0])
                val_list.append(shuffled[1])
            else:
                n_val  = max(1, round(n * vr))
                n_test = max(1, round(n * te))
                n_train = n - n_val - n_test
                if n_train < 1:
                    n_train = 1
                    n_val   = max(1, (n - n_train) // 2)
                    n_test  = n - n_train - n_val

                train_list.extend(shuffled[:n_train])
                val_list.extend(shuffled[n_train:n_train + n_val])
                test_list.extend(shuffled[n_train + n_val:])

        return SplitResult(
            train=train_list,
            val=val_list,
            test=test_list,
            train_ratio=tr,
            val_ratio=vr,
            test_ratio=te,
        )

    def run(
        self,
        records: list[TraceRecord],
        scrub_pii: bool | None = None,
    ) -> FilterResult:
        """
        전체 필터 파이프라인 실행.

        1. tier 필터
        2. MinHash dedup
        3. (선택) PII 스크럽 — render_output에서 PII 마스킹
        4. stratified split
        """
        do_scrub = scrub_pii if scrub_pii is not None else self.scrub_pii

        # 1. tier 필터
        tier_passed, tier_removed = self.filter_by_tier(records)

        # 2. dedup
        deduped, dedup_stats = self.deduplicate(tier_passed)

        # 3. PII scrub (선택)
        pii_count = 0
        final_records = deduped
        if do_scrub:
            try:
                from literary_system.slm.pii_scrubber import PIIScrubber
                scrubber = PIIScrubber()
                scrubbed_records = []
                for r in deduped:
                    new_output = {}
                    had_pii = False
                    for k, v in r.render_output.items():
                        clean, report = scrubber.scrub(v)
                        new_output[k] = clean
                        if not report.is_clean:
                            had_pii = True
                    if had_pii:
                        pii_count += 1
                        import dataclasses
                        r = dataclasses.replace(r, render_output=new_output)
                    scrubbed_records.append(r)
                final_records = scrubbed_records
            except ImportError:
                pass  # PIIScrubber unavailable — skip silently

        # 4. split
        split = self.stratified_split(final_records)

        return FilterResult(
            split=split,
            dedup_stats=dedup_stats,
            tier_filtered=tier_removed,
            pii_scrubbed=pii_count,
            allowed_tiers=[str(t) for t in self.allowed_tiers],
            config={
                "dedup_threshold": self.dedup_threshold,
                "train_ratio":     self.train_ratio,
                "val_ratio":       self.val_ratio,
                "test_ratio":      self.test_ratio,
                "scrub_pii":       do_scrub,
            },
        )
