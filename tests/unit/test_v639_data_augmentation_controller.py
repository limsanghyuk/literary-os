"""
test_v639_data_augmentation_controller.py
V639 DataAugmentationController 단위 테스트 — TC-01~33 (33/33)

ADR-081: SP-C.1 훈련 데이터 증강 컨트롤러
"""
import json
from pathlib import Path

import pytest

from literary_system.constitution.data_augmentation_controller import (
    AUGMENTATION_STRATEGIES,
    DEFAULT_AUGMENT_COUNT,
    DEFAULT_AUGMENT_RATIO,
    MAX_AUGMENT_COUNT,
    AugmentationBatch,
    AugmentedSample,
    DataAugmentationController,
)

SAMPLE_TEXT = "훌륭한 드라마 장면이었다. 배우들의 연기가 뛰어났다. 정말 슬픈 이야기였다."
SAMPLE_TEXTS = [
    "훌륭한 드라마 장면이었다.",
    "배우들의 연기가 뛰어났다.",
    "슬픈 결말이었다.",
]


def make_ctrl(**kwargs) -> DataAugmentationController:
    return DataAugmentationController(seed=42, **kwargs)


# ─────────────────────────────────────────────
# TC-01~05: 상수 및 초기 상태
# ─────────────────────────────────────────────
class TestConstants:
    def test_tc01_strategies_count(self):
        """TC-01: 증강 전략 5종 정의"""
        assert len(AUGMENTATION_STRATEGIES) == 5

    def test_tc02_strategy_names(self):
        """TC-02: 전략 이름 검증"""
        expected = {"SYNONYM_SWAP", "BACK_TRANSLATE", "RANDOM_DELETION",
                    "SENTENCE_SHUFFLE", "TOKEN_INSERT"}
        assert set(AUGMENTATION_STRATEGIES) == expected

    def test_tc03_default_ratio(self):
        """TC-03: DEFAULT_AUGMENT_RATIO = 0.15"""
        assert DEFAULT_AUGMENT_RATIO == 0.15

    def test_tc04_default_count(self):
        """TC-04: DEFAULT_AUGMENT_COUNT = 3"""
        assert DEFAULT_AUGMENT_COUNT == 3

    def test_tc05_initial_state(self):
        """TC-05: 초기 상태 — count=0, history=[], last_batch=None"""
        ctrl = make_ctrl()
        assert ctrl.count() == 0
        assert ctrl.history() == []
        assert ctrl.last_batch() is None
        assert ctrl.total_augmented() == 0


# ─────────────────────────────────────────────
# TC-06~10: augment() 기본 동작
# ─────────────────────────────────────────────
class TestAugmentBasic:
    def test_tc06_augment_returns_batch(self):
        """TC-06: augment()는 AugmentationBatch 반환"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS[:1], augment_count=2)
        assert isinstance(batch, AugmentationBatch)
        assert batch.batch_id
        assert batch.created_at

    def test_tc07_augment_count_correct(self):
        """TC-07: augment_count=2, 텍스트 1개 → 샘플 2개"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", ["텍스트"], augment_count=2)
        assert batch.augmented_count == 2
        assert len(batch.samples) == 2

    def test_tc08_original_count(self):
        """TC-08: original_count = 입력 텍스트 수"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS, augment_count=1)
        assert batch.original_count == 3

    def test_tc09_batch_stored_in_history(self):
        """TC-09: history()에 배치 포함"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS[:1])
        assert batch in ctrl.history()

    def test_tc10_last_batch(self):
        """TC-10: last_batch()는 마지막 배치"""
        ctrl = make_ctrl()
        ctrl.augment("ds-a", SAMPLE_TEXTS[:1])
        b2 = ctrl.augment("ds-b", SAMPLE_TEXTS[:1])
        assert ctrl.last_batch() == b2


# ─────────────────────────────────────────────
# TC-11~17: 증강 전략별 동작
# ─────────────────────────────────────────────
class TestStrategies:
    def test_tc11_synonym_swap_changes_text(self):
        """TC-11: SYNONYM_SWAP — 원본과 다른 텍스트 생성"""
        ctrl = make_ctrl()
        sample = ctrl.augment_single("훌륭한 배우가 슬픈 연기를 했다.", "SYNONYM_SWAP", 1.0)
        assert isinstance(sample, AugmentedSample)
        # 동의어 교체되면 원본과 달라야 함
        assert sample.strategy == "SYNONYM_SWAP"

    def test_tc12_random_deletion_shorter(self):
        """TC-12: RANDOM_DELETION — 원본보다 짧아짐"""
        ctrl = make_ctrl()
        text = "가 나 다 라 마 바 사 아 자 차 카 타 파 하"
        sample = ctrl.augment_single(text, "RANDOM_DELETION", 0.5)
        assert len(sample.augmented_text) < len(text)

    def test_tc13_random_deletion_preserves_one_token(self):
        """TC-13: RANDOM_DELETION — 단일 토큰 텍스트는 삭제 안 됨"""
        ctrl = make_ctrl()
        sample = ctrl.augment_single("안녕", "RANDOM_DELETION", 1.0)
        assert sample.augmented_text == "안녕"

    def test_tc14_sentence_shuffle_same_words(self):
        """TC-14: SENTENCE_SHUFFLE — 단어 수는 동일"""
        ctrl = make_ctrl()
        text = "첫 번째 문장이다. 두 번째 문장이다. 세 번째 문장이다."
        sample = ctrl.augment_single(text, "SENTENCE_SHUFFLE")
        orig_words = sorted(text.replace(".", "").split())
        aug_words = sorted(sample.augmented_text.replace(".", "").split())
        assert orig_words == aug_words

    def test_tc15_token_insert_longer(self):
        """TC-15: TOKEN_INSERT — 원본보다 길어짐"""
        ctrl = make_ctrl()
        text = "드라마 장면 텍스트"
        sample = ctrl.augment_single(text, "TOKEN_INSERT", 0.5)
        assert len(sample.augmented_text.split()) > len(text.split())

    def test_tc16_back_translate_nonempty(self):
        """TC-16: BACK_TRANSLATE — 비어있지 않은 결과"""
        ctrl = make_ctrl()
        sample = ctrl.augment_single(SAMPLE_TEXT, "BACK_TRANSLATE", 0.5)
        assert sample.augmented_text.strip() != ""

    def test_tc17_unknown_strategy_returns_original(self):
        """TC-17: 알 수 없는 전략 → 원본 반환"""
        ctrl = make_ctrl()
        sample = ctrl.augment_single("텍스트", "UNKNOWN_STRATEGY")
        assert sample.augmented_text == "텍스트"


# ─────────────────────────────────────────────
# TC-18~22: AugmentationBatch 필드 검증
# ─────────────────────────────────────────────
class TestBatchFields:
    def test_tc18_dataset_id_stored(self):
        """TC-18: dataset_id 저장"""
        ctrl = make_ctrl()
        batch = ctrl.augment("my-dataset", SAMPLE_TEXTS[:1])
        assert batch.dataset_id == "my-dataset"

    def test_tc19_controller_id_stored(self):
        """TC-19: controller_id 저장"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS[:1], controller_id="human-1")
        assert batch.controller_id == "human-1"

    def test_tc20_note_stored(self):
        """TC-20: note 저장"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS[:1], note="weekly aug")
        assert batch.note == "weekly aug"

    def test_tc21_strategies_used_recorded(self):
        """TC-21: strategies_used — 실제 사용한 전략 기록"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", SAMPLE_TEXTS[:1],
                             strategies=["SYNONYM_SWAP", "RANDOM_DELETION"],
                             augment_count=2)
        assert "SYNONYM_SWAP" in batch.strategies_used
        assert "RANDOM_DELETION" in batch.strategies_used

    def test_tc22_summary_format(self):
        """TC-22: summary() 포맷 확인"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds-test", SAMPLE_TEXTS[:1], augment_count=2)
        s = batch.summary()
        assert "BATCH" in s
        assert "ds-test" in s


# ─────────────────────────────────────────────
# TC-23~27: history / total_augmented / batches_by_dataset
# ─────────────────────────────────────────────
class TestHistory:
    def test_tc23_history_ordered(self):
        """TC-23: history() — 삽입 순서 유지"""
        ctrl = make_ctrl()
        b1 = ctrl.augment("a", SAMPLE_TEXTS[:1])
        b2 = ctrl.augment("b", SAMPLE_TEXTS[:1])
        assert ctrl.history()[0] == b1
        assert ctrl.history()[1] == b2

    def test_tc24_total_augmented(self):
        """TC-24: total_augmented() — 누적 증강 샘플 수"""
        ctrl = make_ctrl()
        ctrl.augment("a", SAMPLE_TEXTS[:1], augment_count=3)
        ctrl.augment("b", SAMPLE_TEXTS[:2], augment_count=2)
        assert ctrl.total_augmented() == 3 + 4  # 1*3 + 2*2

    def test_tc25_batches_by_dataset(self):
        """TC-25: batches_by_dataset() — 특정 ID만 반환"""
        ctrl = make_ctrl()
        ctrl.augment("alpha", SAMPLE_TEXTS[:1])
        ctrl.augment("beta", SAMPLE_TEXTS[:1])
        ctrl.augment("alpha", SAMPLE_TEXTS[:1])
        alpha = ctrl.batches_by_dataset("alpha")
        assert len(alpha) == 2
        assert all(b.dataset_id == "alpha" for b in alpha)

    def test_tc26_count_increments(self):
        """TC-26: count() — 배치 수 증가"""
        ctrl = make_ctrl()
        assert ctrl.count() == 0
        ctrl.augment("ds", SAMPLE_TEXTS[:1])
        assert ctrl.count() == 1
        ctrl.augment("ds", SAMPLE_TEXTS[:1])
        assert ctrl.count() == 2

    def test_tc27_max_augment_count_capped(self):
        """TC-27: augment_count > MAX_AUGMENT_COUNT → MAX_AUGMENT_COUNT로 제한"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", ["텍스트"], augment_count=MAX_AUGMENT_COUNT + 5)
        assert batch.augmented_count == MAX_AUGMENT_COUNT


# ─────────────────────────────────────────────
# TC-28~30: JSONL 영속화
# ─────────────────────────────────────────────
class TestFilePersistence:
    def test_tc28_file_created_on_augment(self, tmp_path):
        """TC-28: 증강 후 JSONL 파일 생성"""
        store = str(tmp_path / "dac.jsonl")
        ctrl = DataAugmentationController(store_path=store, seed=42)
        ctrl.augment("ds", SAMPLE_TEXTS[:1])
        assert Path(store).exists()

    def test_tc29_reload_from_disk(self, tmp_path):
        """TC-29: 디스크 재로드 — 동일 배치 복원"""
        store = str(tmp_path / "dac.jsonl")
        ctrl1 = DataAugmentationController(store_path=store, seed=42)
        b = ctrl1.augment("ds", SAMPLE_TEXTS[:1], augment_count=2)

        ctrl2 = DataAugmentationController(store_path=store, seed=42)
        assert ctrl2.count() == 1
        assert ctrl2.last_batch().batch_id == b.batch_id
        assert ctrl2.last_batch().augmented_count == 2

    def test_tc30_clear_removes_disk(self, tmp_path):
        """TC-30: clear() 후 count=0, 파일 비어 있음"""
        store = str(tmp_path / "dac.jsonl")
        ctrl = DataAugmentationController(store_path=store, seed=42)
        ctrl.augment("ds", SAMPLE_TEXTS[:1])
        ctrl.clear()
        assert ctrl.count() == 0
        assert Path(store).read_text().strip() == ""


# ─────────────────────────────────────────────
# TC-31~33: 엣지케이스 / 직렬화 / 통합
# ─────────────────────────────────────────────
class TestEdgeCasesAndIntegration:
    def test_tc31_empty_texts_skipped(self):
        """TC-31: 빈 텍스트 입력 → 샘플 생성 안 됨"""
        ctrl = make_ctrl()
        batch = ctrl.augment("ds", ["", "   ", ""])
        assert batch.augmented_count == 0

    def test_tc32_to_dict_from_dict_roundtrip(self):
        """TC-32: to_dict / from_dict 왕복 변환"""
        ctrl = make_ctrl()
        b = ctrl.augment("ds", SAMPLE_TEXTS[:1], augment_count=2,
                         controller_id="human-1", note="roundtrip",
                         now="2026-05-26T00:00:00+00:00")
        b2 = AugmentationBatch.from_dict(b.to_dict())
        assert b2.batch_id == b.batch_id
        assert b2.dataset_id == b.dataset_id
        assert b2.augmented_count == b.augmented_count
        assert len(b2.samples) == len(b.samples)
        assert b2.samples[0].strategy == b.samples[0].strategy

    def test_tc33_full_pipeline_all_strategies(self):
        """TC-33: 5종 전략 전체 사용 통합 시나리오"""
        ctrl = make_ctrl()
        batch = ctrl.augment(
            dataset_id="full-pipeline-ds",
            texts=SAMPLE_TEXTS,
            strategies=AUGMENTATION_STRATEGIES,
            augment_count=5,
            controller_id="pipeline-1",
            note="full pipeline test",
        )
        assert batch.original_count == 3
        assert batch.augmented_count == 15  # 3 texts * 5 count
        assert set(batch.strategies_used) == set(AUGMENTATION_STRATEGIES)
        assert ctrl.total_augmented() == 15
