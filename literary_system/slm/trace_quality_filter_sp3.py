"""
literary_system/slm/trace_quality_filter_sp3.py
V492: TraceQualityFilter SP3 확장 레이어

기존 TraceQualityFilter(TraceRecord 기반)를 감싸는 dict 기반 SP3 인터페이스.
SLM 수출 파이프라인에서 임의의 씬 텍스트 레코드를 처리한다.

ADR-008 준수:
  - PII 마스킹 (PIIScrubber 연동)
  - 품질 임계값 필터
  - MinHash 중복 제거
  - Stratified train/val/test 분리
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── 기본 상수 ──────────────────────────────────────────────────────────
DEFAULT_MIN_QUALITY   = 0.4
DEFAULT_DEDUP_THRESHOLD = 0.85
DEFAULT_TRAIN_RATIO   = 0.8
DEFAULT_VAL_RATIO     = 0.1
DEFAULT_TEST_RATIO    = 0.1
SHINGLE_SIZE          = 3          # 토큰 n-gram 크기
MINHASH_PERMUTATIONS  = 64        # MinHash 퍼뮤테이션 수


# ── 헬퍼: MinHash ───────────────────────────────────────────────────────
def _tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())


def _shingles(tokens: List[str], k: int = SHINGLE_SIZE) -> List[str]:
    return [" ".join(tokens[i:i+k]) for i in range(max(1, len(tokens) - k + 1))]


def _minhash(shingles: List[str], n_perm: int = MINHASH_PERMUTATIONS) -> List[int]:
    """간단한 MinHash 서명 (정수 해시 기반)."""
    seeds = list(range(n_perm))
    sig = [2**32 - 1] * n_perm
    for s in shingles:
        base = int(hashlib.md5(s.encode()).hexdigest(), 16)
        for i, seed in enumerate(seeds):
            h = (base ^ (seed * 2654435761)) & 0xFFFFFFFF
            if h < sig[i]:
                sig[i] = h
    return sig


def jaccard_estimate(sig_a: List[int], sig_b: List[int]) -> float:
    matches = sum(a == b for a, b in zip(sig_a, sig_b))
    return matches / len(sig_a)


# ── 데이터 타입 ────────────────────────────────────────────────────────
@dataclass
class SP3Record:
    """SP3 SLM 수출용 레코드 (dict 래퍼)."""
    id:            str
    text:          str
    quality_score: float = 1.0
    tier:          str   = "A"        # A/B/C
    opt_in:        bool  = True
    license:       str   = "internal"
    metadata:      Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SP3Record":
        return cls(
            id            = str(d.get("id", "")),
            text          = str(d.get("text", "")),
            quality_score = float(d.get("quality_score", 1.0)),
            tier          = str(d.get("tier", "A")),
            opt_in        = bool(d.get("opt_in", True)),
            license       = str(d.get("license", "internal")),
            metadata      = {k: v for k, v in d.items()
                             if k not in ("id","text","quality_score","tier","opt_in","license")},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "text": self.text,
            "quality_score": self.quality_score, "tier": self.tier,
            "opt_in": self.opt_in, "license": self.license,
            **self.metadata,
        }


@dataclass
class DedupReport:
    original_count:  int
    kept_count:      int
    removed_count:   int
    threshold:       float

    @property
    def removal_rate(self) -> float:
        if self.original_count == 0:
            return 0.0
        return self.removed_count / self.original_count

    def summary(self) -> str:
        return (f"dedup: {self.original_count}→{self.kept_count} "
                f"(제거율 {self.removal_rate:.1%}, 임계값 {self.threshold})")


@dataclass
class SP3FilterResult:
    """SP3 필터 결과."""
    train:          List[SP3Record]
    val:            List[SP3Record]
    test:           List[SP3Record]
    dedup_report:   DedupReport
    quality_removed: int
    tier_removed:   int
    pii_scrubbed:   int
    config:         Dict[str, Any] = field(default_factory=dict)

    @property
    def total_kept(self) -> int:
        return len(self.train) + len(self.val) + len(self.test)

    def summary(self) -> str:
        return (
            f"SP3FilterResult | train={len(self.train)} val={len(self.val)} "
            f"test={len(self.test)} | quality_removed={self.quality_removed} "
            f"tier_removed={self.tier_removed} pii_scrubbed={self.pii_scrubbed} | "
            f"{self.dedup_report.summary()}"
        )

    def export_jsonl(self, split: str = "train") -> str:
        """지정 split을 JSONL 문자열로 직렬화."""
        records = {"train": self.train, "val": self.val, "test": self.test}[split]
        return "\n".join(json.dumps(r.to_dict(), ensure_ascii=False) for r in records)

    def counts(self) -> Dict[str, int]:
        return {
            "train": len(self.train), "val": len(self.val), "test": len(self.test),
            "quality_removed": self.quality_removed, "tier_removed": self.tier_removed,
            "pii_scrubbed": self.pii_scrubbed,
        }


# ── 핵심 클래스 ─────────────────────────────────────────────────────────
class TraceQualityFilterSP3:
    """
    SP3 SLM 수출용 TraceQualityFilter.

    dict 리스트를 입력받아 ADR-008 준수 4단 필터 + stratified split 수행.
    기존 TraceQualityFilter(TraceRecord 기반)와 병렬로 존재하며 기존 코드를 변경하지 않는다.
    """

    ALLOWED_TIERS     = {"A", "B"}
    ALLOWED_LICENSES  = {"cc-by", "cc-by-sa", "public-domain", "internal", "mit"}

    def __init__(
        self,
        min_quality:       float = DEFAULT_MIN_QUALITY,
        dedup_threshold:   float = DEFAULT_DEDUP_THRESHOLD,
        train_ratio:       float = DEFAULT_TRAIN_RATIO,
        val_ratio:         float = DEFAULT_VAL_RATIO,
        test_ratio:        float = DEFAULT_TEST_RATIO,
        allowed_tiers:     Optional[set] = None,
        allowed_licenses:  Optional[set] = None,
        scrub_pii:         bool = True,
        seed:              int = 42,
    ) -> None:
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "비율 합계 != 1"
        self._min_quality      = min_quality
        self._dedup_threshold  = dedup_threshold
        self._train_ratio      = train_ratio
        self._val_ratio        = val_ratio
        self._test_ratio       = test_ratio
        self._allowed_tiers    = allowed_tiers or self.ALLOWED_TIERS
        self._allowed_licenses = allowed_licenses or self.ALLOWED_LICENSES
        self._scrub_pii        = scrub_pii
        self._rng              = random.Random(seed)

    # ── 단계별 필터 ─────────────────────────────────────────────────────

    def _filter_quality(self, records: List[SP3Record]) -> Tuple[List[SP3Record], int]:
        kept = [r for r in records if r.quality_score >= self._min_quality]
        return kept, len(records) - len(kept)

    def _filter_tier(self, records: List[SP3Record]) -> Tuple[List[SP3Record], int]:
        kept = [r for r in records
                if r.tier in self._allowed_tiers
                and r.opt_in
                and r.license in self._allowed_licenses]
        return kept, len(records) - len(kept)

    def _scrub(self, records: List[SP3Record]) -> Tuple[List[SP3Record], int]:
        """간단한 PII 마스킹 (PIIScrubberSP3 연동 또는 내장 패턴)."""
        if not self._scrub_pii:
            return records, 0
        pii_patterns = [
            (re.compile(r'\d{6}-[1-4]\d{6}'), '[주민번호]'),
            (re.compile(r'01[016789]-?\d{3,4}-?\d{4}'), '[전화번호]'),
            (re.compile(r'\b\d{3}-\d{2}-\d{5}\b'), '[사업자번호]'),
            (re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'), '[이메일]'),
        ]
        scrubbed_count = 0
        result = []
        for r in records:
            text = r.text
            changed = False
            for pat, repl in pii_patterns:
                new_text = pat.sub(repl, text)
                if new_text != text:
                    text = new_text
                    changed = True
            if changed:
                scrubbed_count += 1
                r = SP3Record(id=r.id, text=text, quality_score=r.quality_score,
                               tier=r.tier, opt_in=r.opt_in, license=r.license,
                               metadata=r.metadata)
            result.append(r)
        return result, scrubbed_count

    def _deduplicate(self, records: List[SP3Record]) -> Tuple[List[SP3Record], DedupReport]:
        """MinHash 기반 중복 제거."""
        sigs: List[List[int]] = []
        kept_indices: List[int] = []
        for i, r in enumerate(records):
            tokens = _tokenize(r.text)
            shingles = _shingles(tokens)
            sig = _minhash(shingles)
            is_dup = False
            for ki in kept_indices:
                if jaccard_estimate(sig, sigs[ki]) >= self._dedup_threshold:
                    is_dup = True
                    break
            if not is_dup:
                sigs.append(sig)
                kept_indices.append(i)
            else:
                sigs.append(sig)  # 인덱스 정렬 유지
        kept = [records[i] for i in kept_indices]
        report = DedupReport(
            original_count=len(records), kept_count=len(kept),
            removed_count=len(records) - len(kept),
            threshold=self._dedup_threshold,
        )
        return kept, report

    def _split(self, records: List[SP3Record]) -> Tuple[List[SP3Record], List[SP3Record], List[SP3Record]]:
        """Stratified split — tier 기준 층화 추출."""
        by_tier: Dict[str, List[SP3Record]] = {}
        for r in records:
            by_tier.setdefault(r.tier, []).append(r)

        train, val, test = [], [], []
        for tier_recs in by_tier.values():
            self._rng.shuffle(tier_recs)
            n = len(tier_recs)
            n_train = max(1, round(n * self._train_ratio)) if n > 1 else 1
            n_val   = max(0, round(n * self._val_ratio))
            train.extend(tier_recs[:n_train])
            val.extend(tier_recs[n_train:n_train + n_val])
            test.extend(tier_recs[n_train + n_val:])
        return train, val, test

    # ── 메인 API ────────────────────────────────────────────────────────

    def run(self, records: List[Dict[str, Any]]) -> SP3FilterResult:
        """
        dict 리스트를 입력받아 SP3FilterResult 반환.

        파이프라인:
          1. dict → SP3Record 변환
          2. 품질 필터
          3. 티어/옵트인/라이선스 필터 (ADR-008)
          4. PII 마스킹 (ADR-008)
          5. MinHash 중복 제거
          6. Stratified train/val/test split
        """
        sp3_records = [SP3Record.from_dict(d) for d in records]

        sp3_records, quality_removed = self._filter_quality(sp3_records)
        sp3_records, tier_removed    = self._filter_tier(sp3_records)
        sp3_records, pii_scrubbed    = self._scrub(sp3_records)
        sp3_records, dedup_report    = self._deduplicate(sp3_records)
        train, val, test             = self._split(sp3_records)

        return SP3FilterResult(
            train=train, val=val, test=test,
            dedup_report=dedup_report,
            quality_removed=quality_removed,
            tier_removed=tier_removed,
            pii_scrubbed=pii_scrubbed,
            config={
                "min_quality": self._min_quality,
                "dedup_threshold": self._dedup_threshold,
                "train_ratio": self._train_ratio,
                "val_ratio": self._val_ratio,
                "test_ratio": self._test_ratio,
            },
        )

    def export_jsonl(
        self,
        result: SP3FilterResult,
        output_dir: str,
        prefix: str = "sp3",
    ) -> Dict[str, str]:
        """train/val/test를 JSONL 파일로 저장."""
        out = pathlib.Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = {}
        for split_name in ("train", "val", "test"):
            fp = out / f"{prefix}_{split_name}.jsonl"
            fp.write_text(result.export_jsonl(split_name), encoding="utf-8")
            paths[split_name] = str(fp)
        return paths
