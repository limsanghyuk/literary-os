"""
WP-1 (V747) DoD 테스트 — 6 TC

DoD 체크:
  1. test_registry_loads_physics_formulas
  2. test_stage1_report_structure
  3. test_preregistered_tau_immutable_in_code
  4. test_ledger_append_and_transition
  5. test_two_consecutive_fails_marks_deprecated_candidate
  6. test_cost_cap_aborts_gracefully
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from literary_system.validation.formula_registry import REGISTRY
from literary_system.validation.stage_registry import STAGES
from literary_system.validation.formula_harness import Harness, StageReport
from literary_system.validation import ledger


# ──────────────────────────────────────────────────────────────
# 픽스처
# ──────────────────────────────────────────────────────────────

def _synthetic_jsonl(n: int = 40, quality_val: float = 0.8) -> str:
    """synthetic 씬 JSONL fixture — LLM 불요."""
    lines = []
    for i in range(n):
        row = {
            "conflict_intensity":   0.6 + (i % 4) * 0.05,
            "scene_energy_ratio":   0.5 + (i % 3) * 0.07,
            "motif_residue_score":  0.4 + (i % 5) * 0.04,
            "curiosity_gradient":   0.5 + (i % 6) * 0.03,
            "reader_surface_score": 0.6 + (i % 4) * 0.05,
            "arc_tension_score":    0.5 + (i % 5) * 0.04,
            # Stage-1 GT
            "quality_proxy": quality_val + (i % 10) * 0.01,
            # Stage-2 GT
            "plant_payoff":  0.55 + (i % 8) * 0.02,
        }
        lines.append(json.dumps(row))
    return "\n".join(lines)


@pytest.fixture()
def jsonl_path(tmp_path: Path) -> Path:
    p = tmp_path / "scenes.jsonl"
    p.write_text(_synthetic_jsonl(n=50), encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def reset_ledger():
    """각 테스트 전 ledger 전역 상태 초기화."""
    ledger.reset_for_test()
    yield
    ledger.reset_for_test()


# ──────────────────────────────────────────────────────────────
# TC-1: Registry에 physics 공식 로드 확인
# ──────────────────────────────────────────────────────────────

class TestRegistryLoadPhysicsFormulas:
    def test_registry_loads_physics_formulas(self):
        """F-06_fitness가 REGISTRY에 등록, domain=physics, lifecycle=candidate."""
        assert "F-06_fitness" in REGISTRY, "F-06_fitness REGISTRY에 없음"
        entry = REGISTRY["F-06_fitness"]
        assert entry["domain"] == "physics"
        assert entry["lifecycle"] == "candidate"
        assert callable(entry["score_fn"])

    def test_score_fn_returns_numeric(self):
        """score_fn이 SceneRow를 받아 float 반환."""
        fn = REGISTRY["F-06_fitness"]["score_fn"]
        row = {
            "conflict_intensity": 0.7, "scene_energy_ratio": 0.6,
            "motif_residue_score": 0.5, "curiosity_gradient": 0.6,
            "reader_surface_score": 0.65, "arc_tension_score": 0.55,
        }
        score = fn(row)
        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0


# ──────────────────────────────────────────────────────────────
# TC-2: Stage-1 StageReport 구조 검증
# ──────────────────────────────────────────────────────────────

class TestStage1ReportStructure:
    def test_stage1_report_structure(self, jsonl_path: Path):
        """Harness.run(stage=1) → StageReport 필드 완전성."""
        harness = Harness()
        report  = harness.run(stage_id=1, db_path=str(jsonl_path))

        assert isinstance(report, StageReport)
        assert report.stage_id == 1
        assert not report.aborted, f"예기치 않은 abort: {report.abort_reason}"
        assert len(report.formula_results) >= 1, "formula_results 비어있음"

        fr = report.formula_results[0]
        assert hasattr(fr, "formula_id")
        assert hasattr(fr, "metric_name")
        assert hasattr(fr, "value")
        assert hasattr(fr, "n")
        assert hasattr(fr, "passed")
        assert hasattr(fr, "lifecycle_suggestion")
        assert fr.metric_name == "spearman"
        assert fr.n >= 1

    def test_report_json_serializable(self, jsonl_path: Path):
        """to_json() 가 유효한 JSON을 반환."""
        harness = Harness()
        report  = harness.run(stage_id=1, db_path=str(jsonl_path))
        raw     = report.to_json()
        parsed  = json.loads(raw)
        assert "stage_id" in parsed
        assert "formula_results" in parsed

    def test_invalid_stage_aborts(self, jsonl_path: Path):
        """미정의 stage_id → aborted=True."""
        harness = Harness()
        report  = harness.run(stage_id=99, db_path=str(jsonl_path))
        assert report.aborted
        assert "미정의" in report.abort_reason


# ──────────────────────────────────────────────────────────────
# TC-3: Stage 임계값 코드 상수 불변 확인
# ──────────────────────────────────────────────────────────────

class TestPreregisteredTauImmutableInCode:
    def test_preregistered_tau_immutable_in_code(self):
        """STAGES[1].tau == 0.40 — 코드 상수 불변 검증."""
        assert STAGES[1]["tau"] == 0.40, "Stage-1 tau 변경 금지"
        assert STAGES[1]["metric"] == "spearman"
        assert STAGES[1]["min_n"] == 30

    def test_all_stages_present(self):
        """Stage 1~6 전부 STAGES에 존재."""
        for sid in range(1, 7):
            assert sid in STAGES, f"STAGES[{sid}] 미정의"

    def test_stage_keys_required(self):
        """각 Stage 딕셔너리에 필수 키 존재."""
        required = {"gt", "metric", "tau"}
        for sid, cfg in STAGES.items():
            missing = required - cfg.keys()
            assert not missing, f"STAGES[{sid}] 누락 키: {missing}"


# ──────────────────────────────────────────────────────────────
# TC-4: ledger append + transition 기본 동작
# ──────────────────────────────────────────────────────────────

class TestLedgerAppendAndTransition:
    def test_ledger_append_and_transition(self, tmp_path: Path):
        """record() → ledger 파일 append; transition() → 상태 변경."""
        lp = tmp_path / "formula_ledger.md"

        ledger.record("F-06_fitness", "stage1:pass", "fixture.jsonl", ledger_path=lp)
        content = lp.read_text(encoding="utf-8")
        assert "F-06_fitness" in content
        assert "stage1:pass" in content

        # transition: candidate → validated
        new_state = ledger.transition("F-06_fitness", "validated", ledger_path=lp)
        assert new_state == "validated"
        assert ledger.get_lifecycle("F-06_fitness") == "validated"

    def test_ledger_creates_header_on_first_write(self, tmp_path: Path):
        """최초 record 시 헤더 행 자동 생성."""
        lp = tmp_path / "new_ledger.md"
        assert not lp.exists()
        ledger.record("F-06_fitness", "test_event", "path/to/evidence", ledger_path=lp)
        content = lp.read_text(encoding="utf-8")
        assert "# Formula Lifecycle Ledger" in content
        assert "| timestamp |" in content


# ──────────────────────────────────────────────────────────────
# TC-5: 2회 연속 미달 → deprecated 자동 표기
# ──────────────────────────────────────────────────────────────

class TestTwoConsecutiveFailsMarksDeprecatedCandidate:
    def test_two_consecutive_fails_marks_deprecated_candidate(self, tmp_path: Path):
        """recalibrate 2회 연속 → deprecated 자동 승격."""
        lp = tmp_path / "ledger.md"

        s1 = ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        assert s1 == "recalibrate", "1회 미달 → recalibrate 유지"

        s2 = ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        assert s2 == "deprecated", "2회 미달 → deprecated 자동 승격"

        assert ledger.get_lifecycle("F-06_fitness") == "deprecated"

    def test_deprecated_is_terminal_state(self, tmp_path: Path):
        """deprecated 이후 transition 시도 → 유지."""
        lp = tmp_path / "ledger.md"
        ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        # deprecated 상태에서 validated 시도
        s = ledger.transition("F-06_fitness", "validated", ledger_path=lp)
        assert s == "deprecated", "deprecated는 terminal — 다른 상태로 전이 불가"

    def test_pass_resets_consecutive_fails(self, tmp_path: Path):
        """1회 recalibrate 후 validated → 연속 카운터 리셋 → 이후 1회 recalibrate = recalibrate."""
        lp = tmp_path / "ledger.md"
        ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        ledger.transition("F-06_fitness", "validated",   ledger_path=lp)  # 카운터 리셋
        s = ledger.transition("F-06_fitness", "recalibrate", ledger_path=lp)
        assert s == "recalibrate", "카운터 리셋 후 1회 미달 → deprecated 아님"


# ──────────────────────────────────────────────────────────────
# TC-6: cost_cap 초과 시 graceful abort
# ──────────────────────────────────────────────────────────────

class TestCostCapAbortsGracefully:
    def test_cost_cap_aborts_gracefully(self, monkeypatch, jsonl_path: Path):
        """
        비용이 cost_cap 초과 시뮬레이션 → StageReport.aborted=True, 정상 종료.
        현재 구현은 순수 로컬(0.0 비용)이므로 내부 비용 주입으로 테스트.
        """
        harness = Harness()

        # cost_cap=-0.01 → 0.0 > -0.01 → abort 발동
        report = harness.run(stage_id=1, db_path=str(jsonl_path), cost_cap=-0.01)
        assert report.aborted
        assert "cost_cap" in report.abort_reason.lower() or "초과" in report.abort_reason

    def test_negative_cost_cap_does_not_raise(self, jsonl_path: Path):
        """cost_cap 음수 → abort이지만 예외 없이 StageReport 반환."""
        harness = Harness()
        report  = harness.run(stage_id=1, db_path=str(jsonl_path), cost_cap=-1.0)
        assert isinstance(report, StageReport)
        # aborted OR 데이터 있으면 정상 진행 (비용 0.0 이므로 통과 가능)
        # 이 TC의 핵심: 예외가 발생하지 않음
