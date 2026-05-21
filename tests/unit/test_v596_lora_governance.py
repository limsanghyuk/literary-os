"""V596 TC: LoRA Dataset Pipeline + Governance (11 TC).

TC-A1~A3: LoRAProvenanceLedger
TC-B1~B2: DSRHandler
TC-C1~C3: LoRADatasetBuilder
TC-D1~D2: DatasetSplitter
TC-E1: DatasetRegistry
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    entry_id: str,
    text: str = "씬 텍스트",
    genre: str = "멜로",
    title: str = "작품명",
    source_type: str = "synthetic",
    license: str = "CC-BY-4.0",
) -> Dict[str, Any]:
    return {
        "entry_id": entry_id,
        "text": text,
        "genre": genre,
        "title": title,
        "source_type": source_type,
        "license": license,
    }


def _make_entries(n: int) -> List[Dict]:
    return [_make_entry(f"e-{i}", text=f"씬 텍스트 {i}") for i in range(n)]


# ---------------------------------------------------------------------------
# TC-A: LoRAProvenanceLedger
# ---------------------------------------------------------------------------

class TestLoRAProvenanceLedger:

    def test_a1_chain_integrity(self):
        """TC-A1: 여러 레코드 추가 후 verify() PASS."""
        from literary_system.governance.provenance_ledger import LoRAProvenanceLedger, ProvenanceChainError

        ledger = LoRAProvenanceLedger()
        for i in range(5):
            ledger.append(f"entry-{i}", hashlib.sha256(f"content-{i}".encode()).hexdigest()[:16])

        assert len(ledger) == 5
        assert ledger.verify() is True

    def test_a2_dsr_marking(self):
        """TC-A2: DSR 삭제 마킹 후 active_records 에서 제외."""
        from literary_system.governance.provenance_ledger import LoRAProvenanceLedger

        ledger = LoRAProvenanceLedger()
        ledger.append("entry-1", "hash1")
        ledger.append("entry-2", "hash2")
        ledger.append("entry-3", "hash3")

        result = ledger.mark_dsr_deleted("entry-2", "req-001")
        assert result is True
        active = ledger.active_records()
        assert len(active) == 2
        active_ids = {r.entry_id for r in active}
        assert "entry-2" not in active_ids

    def test_a3_save_load(self):
        """TC-A3: JSONL 저장 후 로드 시 체인 무결성 유지."""
        from literary_system.governance.provenance_ledger import LoRAProvenanceLedger

        ledger = LoRAProvenanceLedger()
        ledger.append("e-1", "abc")
        ledger.append("e-2", "def")
        ledger.mark_dsr_deleted("e-1", "req-x")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            ledger.save(path)
            loaded = LoRAProvenanceLedger.load(path)

        assert len(loaded) == 2
        assert loaded.verify() is True
        deleted = [r for r in loaded._records if r.dsr_deleted]
        assert len(deleted) == 1
        assert deleted[0].entry_id == "e-1"


# ---------------------------------------------------------------------------
# TC-B: DSRHandler
# ---------------------------------------------------------------------------

class TestDSRHandler:

    def test_b1_full_lifecycle(self):
        """TC-B1: submit → process(with ledger) → complete 전 수명주기."""
        from literary_system.governance.dsr_handler import DSRHandler, DSRStatus
        from literary_system.governance.provenance_ledger import LoRAProvenanceLedger

        ledger = LoRAProvenanceLedger()
        ledger.append("entry-a", "hash-a")
        ledger.append("entry-b", "hash-b")

        handler = DSRHandler()
        req = handler.submit("user-1", ["entry-a"])

        assert req.status == DSRStatus.PENDING

        handler.process(req.request_id, ledger=ledger)
        assert req.status == DSRStatus.PROCESSING

        handler.complete(req.request_id, notes="처리 완료")
        assert req.status == DSRStatus.COMPLETED

        # ledger에서 entry-a가 삭제 마킹되었는지 확인
        active = {r.entry_id for r in ledger.active_records()}
        assert "entry-a" not in active

    def test_b2_deadline_tracking(self):
        """TC-B2: SLA 만료 시 EXPIRED 전이."""
        from literary_system.governance.dsr_handler import DSRHandler, DSRStatus, DSR_SLA_SECONDS

        handler = DSRHandler()
        req = handler.submit("user-2", ["e-1"])

        # 기한 이후 시각을 now로 전달
        future = req.submitted_at + DSR_SLA_SECONDS + 1
        overdue = handler.overdue_requests(now=future)

        assert len(overdue) == 1
        assert overdue[0].status == DSRStatus.EXPIRED


# ---------------------------------------------------------------------------
# TC-C: LoRADatasetBuilder
# ---------------------------------------------------------------------------

class TestLoRADatasetBuilder:

    def test_c1_basic_build(self):
        """TC-C1: 10개 entry → 10개 LoRASample."""
        from literary_system.finetune.lora_dataset_builder import LoRADatasetBuilder

        entries = _make_entries(10)
        builder = LoRADatasetBuilder()
        samples = builder.build(entries)

        assert len(samples) == 10
        for s in samples:
            assert s.instruction  # non-empty
            assert s.output       # non-empty
            assert len(s.content_hash) == 16

    def test_c2_dsr_exclusion(self):
        """TC-C2: DSR 삭제 entry_id 는 빌드 시 제외."""
        from literary_system.finetune.lora_dataset_builder import LoRADatasetBuilder

        entries = _make_entries(5)
        deleted_ids = {"e-1", "e-3"}
        builder = LoRADatasetBuilder(dsr_deleted_ids=deleted_ids)
        samples = builder.build(entries)

        assert len(samples) == 3
        built_ids = {s.entry_id for s in samples}
        assert "e-1" not in built_ids
        assert "e-3" not in built_ids

    def test_c3_save_load_jsonl(self):
        """TC-C3: JSONL 저장 후 로드 시 동일한 샘플."""
        from literary_system.finetune.lora_dataset_builder import LoRADatasetBuilder

        entries = _make_entries(3)
        builder = LoRADatasetBuilder()
        samples = builder.build(entries)

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "train.jsonl"
            LoRADatasetBuilder.save(samples, path)
            loaded = LoRADatasetBuilder.load(path)

        assert len(loaded) == 3
        assert loaded[0].entry_id == samples[0].entry_id
        assert loaded[0].output == samples[0].output


# ---------------------------------------------------------------------------
# TC-D: DatasetSplitter
# ---------------------------------------------------------------------------

class TestDatasetSplitter:

    def _make_samples(self, n: int):
        from literary_system.finetune.lora_dataset_builder import LoRADatasetBuilder
        entries = _make_entries(n)
        return LoRADatasetBuilder().build(entries)

    def test_d1_ratio_881(self):
        """TC-D1: 1000개 샘플 → 8:1:1 비율 확인."""
        from literary_system.finetune.dataset_splitter import DatasetSplitter, LoRADatasetSplit

        samples = self._make_samples(1000)
        splitter = DatasetSplitter()
        split = splitter.split(samples)

        assert split.total == 1000
        assert split.train == samples[:800] or len(split.train) == 800
        assert len(split.val) == 100
        assert len(split.test) == 100

    def test_d2_reproducibility(self):
        """TC-D2: 동일 seed → 동일 분할."""
        from literary_system.finetune.dataset_splitter import DatasetSplitter, LoRADatasetSplit

        samples = self._make_samples(200)
        splitter = DatasetSplitter(seed=42)
        split1 = splitter.split(samples)
        split2 = splitter.split(samples)

        assert [s.entry_id for s in split1.train] == [s.entry_id for s in split2.train]
        assert [s.entry_id for s in split1.val] == [s.entry_id for s in split2.val]


# ---------------------------------------------------------------------------
# TC-E: DatasetRegistry
# ---------------------------------------------------------------------------

class TestDatasetRegistry:

    def test_e1_register_verify_persist(self):
        """TC-E1: 등록 → sha256 검증 → JSON 저장/로드."""
        from literary_system.finetune.dataset_registry import DatasetRegistry

        with tempfile.TemporaryDirectory() as td:
            # 가짜 JSONL 파일 생성
            data_path = Path(td) / "train.jsonl"
            data_path.write_text('{"instruction":"i","input":"x","output":"y"}\n', encoding="utf-8")
            sha = DatasetRegistry.compute_sha256(data_path)

            registry_path = Path(td) / "registry.json"
            registry = DatasetRegistry(registry_path)
            dv = registry.register(
                version_tag="v1.0",
                split_tag="train",
                path=data_path,
                sha256=sha,
                num_samples=1,
                source_hash="abc123",
            )

            assert registry.verify("v1.0", "train") is True

            registry.save()
            loaded = DatasetRegistry.load(registry_path)
            dv2 = loaded.get("v1.0", "train")
            assert dv2 is not None
            assert dv2.sha256 == sha
            assert dv2.num_samples == 1
