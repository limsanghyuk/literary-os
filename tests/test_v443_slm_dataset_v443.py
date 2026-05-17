"""
V443 tests -- PIIScrubber + SLMDatasetBuilderV443 (ShareGPT + PII)
"""
import json
import tempfile
from pathlib import Path
import pytest
from literary_system.slm.pii_scrubber import PIIScrubber, ScrubReport
from literary_system.slm.dataset_builder_v443 import SLMDatasetBuilderV443
from literary_system.trace.trace_dataset_store import (
    TraceDatasetStore, TraceRecord, PromotionTier, make_trace_record,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_STATE_BEFORE = {"SP": 0.4, "RU": 0.3, "ET": 0.2}
_STATE_AFTER  = {"SP": 0.5, "RU": 0.4, "ET": 0.3}
_READER_EST   = {"reader_pull": 0.60, "ai_smell_score": 0.10}


def _make_record(
    genre="drama",
    user_prompt="scene 0",
    render_text="씬 본문 텍스트 내용",
    L_total=0.10,
    reader_pull=0.60,
    ai_smell=0.10,
    episode_no=1,
    scene_id="sc01",
) -> TraceRecord:
    """make_trace_record 팩토리를 사용해 TraceRecord 생성."""
    return make_trace_record(
        project_id="test_proj",
        episode_no=episode_no,
        scene_id=scene_id,
        seed_contract={"genre": genre, "user_prompt": user_prompt},
        style_dna_profile="압박형",
        macroarc_intent="갈등 심화",
        literary_state_before=_STATE_BEFORE,
        literary_state_after=_STATE_AFTER,
        render_output={scene_id: render_text},
        loss_report={"L_total": L_total},
        reader_estimate={"reader_pull": reader_pull, "ai_smell_score": ai_smell},
        trajectory_deviation=0.05,
        critic_findings=[],
        repair_applied=False,
        hitl_recommended=False,
        knowledge_pressure=0.3,
    )


def _make_store_with_records(n=3):
    """n개의 CANONICAL 레코드를 담은 TraceDatasetStore 반환."""
    # mkdtemp: 호출자 수명 동안 temp dir 유지 (context manager 사용 안 함)
    tmpdir = tempfile.mkdtemp()
    store = TraceDatasetStore(tmpdir)
    for i in range(n):
        r = _make_record(
            user_prompt=f"scene {i}",
            render_text=f"씬 {i} 본문 텍스트 내용",
            L_total=0.10 + i * 0.01,   # 0.10~0.12 → CANONICAL
            scene_id=f"sc{i:02d}",
            episode_no=i + 1,
        )
        store.commit(r)
    return store


# ---------------------------------------------------------------------------
# TestPIIScrubber
# ---------------------------------------------------------------------------

class TestPIIScrubber:
    def test_phone_masked(self):
        s = PIIScrubber()
        text = "전화번호 010-1234-5678 입니다"
        clean, report = s.scrub(text)
        assert "[PHONE]" in clean
        assert "010-1234-5678" not in clean
        assert report.counts.get("phone", 0) == 1

    def test_email_masked(self):
        s = PIIScrubber()
        text = "이메일: user@example.com 로 연락"
        clean, report = s.scrub(text)
        assert "[EMAIL]" in clean
        assert "user@example.com" not in clean

    def test_ssn_masked(self):
        s = PIIScrubber()
        text = "주민번호 123456-1234567 확인"
        clean, report = s.scrub(text)
        assert "[SSN]" in clean
        assert "123456-1234567" not in clean

    def test_credit_card_masked(self):
        s = PIIScrubber()
        text = "카드번호 1234-5678-9012-3456"
        clean, report = s.scrub(text)
        assert "[CARD]" in clean

    def test_clean_text_unchanged(self):
        s = PIIScrubber()
        text = "오늘 날씨가 맑고 화창합니다."
        clean, report = s.scrub(text)
        assert clean == text
        assert report.is_clean
        assert report.total_removed == 0

    def test_multiple_pii_in_one_text(self):
        s = PIIScrubber()
        text = "연락처 010-9999-8888 또는 test@mail.com"
        clean, report = s.scrub(text)
        assert "[PHONE]" in clean
        assert "[EMAIL]" in clean
        assert report.total_removed == 2

    def test_disabled_category(self):
        s = PIIScrubber(disabled={"phone"})
        text = "전화 010-1234-5678"
        clean, report = s.scrub(text)
        assert "010-1234-5678" in clean  # not masked
        assert "phone" not in s.active_categories

    def test_scrub_batch(self):
        s = PIIScrubber()
        texts = ["test@mail.com", "clean text", "010-1234-5678"]
        results = s.scrub_batch(texts)
        assert len(results) == 3
        assert "[EMAIL]" in results[0][0]
        assert results[1][1].is_clean
        assert "[PHONE]" in results[2][0]

    def test_is_clean_true(self):
        s = PIIScrubber()
        assert s.is_clean("일반 텍스트 내용")

    def test_is_clean_false(self):
        s = PIIScrubber()
        assert not s.is_clean("이메일 user@mail.com 포함")

    def test_scrub_report_summary(self):
        s = PIIScrubber()
        text = "전화 010-0000-0000"
        _, report = s.scrub(text)
        assert "phone" in report.summary()

    def test_active_categories_default(self):
        s = PIIScrubber()
        cats = s.active_categories
        assert "phone" in cats
        assert "email" in cats
        assert "ssn" in cats


# ---------------------------------------------------------------------------
# TestSLMDatasetBuilderV443
# ---------------------------------------------------------------------------

class TestSLMDatasetBuilderV443:
    def _make_builder(self, n=3):
        store = _make_store_with_records(n)
        return SLMDatasetBuilderV443(store)

    def test_inherits_alpaca(self):
        b = self._make_builder()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_alpaca_dataset(out)
        assert result["format"] == "alpaca"
        assert result["total_records"] == 3

    def test_sharegpt_format(self):
        b = self._make_builder()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_sharegpt_dataset(out)
        assert result["format"] == "sharegpt"
        assert result["total_records"] == 3

    def test_sharegpt_file_structure(self):
        b = self._make_builder()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        b.build_sharegpt_dataset(out)
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert isinstance(data, list)
        entry = data[0]
        assert "conversations" in entry
        convs = entry["conversations"]
        froms = [c["from"] for c in convs]
        assert "human" in froms
        assert "gpt" in froms

    def test_sharegpt_metadata(self):
        b = self._make_builder()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        b.build_sharegpt_dataset(out)
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        meta = data[0]["metadata"]
        assert "trace_id" in meta
        assert "L_total" in meta
        assert "pii_removed" in meta

    def test_sharegpt_pii_scrub(self):
        store = TraceDatasetStore(tempfile.mkdtemp())
        r = _make_record(
            user_prompt="연락처 010-5555-5555",
            render_text="email: test@test.com 있는 씬",
            scene_id="pii_test",
        )
        store.commit(r)
        b = SLMDatasetBuilderV443(store)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_sharegpt_dataset(out, scrub_pii=True)
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        # PII should be removed from conversations
        all_text = json.dumps(data)
        assert "010-5555-5555" not in all_text
        assert "test@test.com" not in all_text

    def test_sharegpt_no_scrub(self):
        store = TraceDatasetStore(tempfile.mkdtemp())
        r = _make_record(user_prompt="일반 내용", render_text="씬 내용", scene_id="nopii")
        store.commit(r)
        b = SLMDatasetBuilderV443(store)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_sharegpt_dataset(out, scrub_pii=False)
        assert result["total_records"] == 1

    def test_alpaca_scrubbed(self):
        b = self._make_builder()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_alpaca_dataset_scrubbed(out)
        assert result["format"] == "alpaca_scrubbed"
        assert "pii_removed" in result

    def test_quality_filter_applied(self):
        store = _make_store_with_records(5)
        # add low-quality record that should be filtered (L_total=0.99 → ARCHIVE)
        bad = _make_record(
            user_prompt="bad",
            render_text="bad output",
            L_total=0.99,
            reader_pull=0.0,
            ai_smell=0.9,
            scene_id="bad01",
            episode_no=99,
        )
        store.commit(bad)
        b = SLMDatasetBuilderV443(store)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = b.build_sharegpt_dataset(out)
        # bad record filtered out
        assert result["total_records"] == 5
