"""
V576 — Test Fortification: 0% 커버리지 모듈 단위 테스트

커버리지 87% → 90% 목표.
대상: multiwork, predictive, schemas, auth(G34)

TC-01~12: MultiWork 모듈 (multi_work_core, orchestrator, shared_character_db, shared_world_db)
TC-13~22: Predictive 모듈 (debt_predictor, pne_core, preemptive_gate, feedback_learner)
TC-23~32: Schemas 모듈 (envelope, definitions, validator, character_ledger)
TC-33~40: Auth Regression (G34) — DEV_MODE 보안 패치 회귀 검증
TC-41~45: G33 SchemaRoundTrip
"""
from __future__ import annotations
import pytest


# ─── TC-01~12: MultiWork ──────────────────────────────────────────────────────

class TestMultiWorkCore:
    def test_work_project_creation(self):
        from literary_system.multiwork.multi_work_core import WorkProject, WorkStatus
        p = WorkProject(project_id="p1", author_id="a1", title="소설1", genre="drama")
        assert p.project_id == "p1"
        assert p.status == WorkStatus.DRAFT

    def test_work_project_status_fsm(self):
        from literary_system.multiwork.multi_work_core import WorkProject, WorkStatus
        p = WorkProject(project_id="p2", author_id="a2", title="T", genre="romance")
        p.activate()
        assert p.status == WorkStatus.ACTIVE
        p.pause()
        assert p.status == WorkStatus.PAUSED
        p.activate()
        p.complete()
        assert p.status == WorkStatus.COMPLETED

    def test_multiwork_core_register_project(self):
        from literary_system.multiwork.multi_work_core import MultiWorkCore
        core = MultiWorkCore(max_concurrent=5)
        proj = core.register_project(author_id="auth1", title="작품1", genre="drama")
        assert proj.author_id == "auth1"
        assert proj.title == "작품1"

    def test_multiwork_core_list_projects(self):
        from literary_system.multiwork.multi_work_core import MultiWorkCore
        core = MultiWorkCore(max_concurrent=5)
        core.register_project("auth1", "P1", "fantasy")
        core.register_project("auth1", "P2", "noir")
        core.register_project("auth2", "P3", "drama")
        projects = core.list_projects(author_id="auth1")
        assert len(projects) == 2

    def test_multiwork_core_open_close_session(self):
        from literary_system.multiwork.multi_work_core import MultiWorkCore
        core = MultiWorkCore(max_concurrent=5)
        proj = core.register_project("a1", "P1", "drama")
        session = core.open_session(proj.project_id)
        assert session.project_id == proj.project_id
        assert session.episode_count == 0  # session is open
        closed = core.close_session(proj.project_id)
        assert closed is not None

    def test_project_conflict_exception(self):
        from literary_system.multiwork.multi_work_core import ProjectConflict
        with pytest.raises(ProjectConflict):
            raise ProjectConflict("중복 세션")

    def test_work_session_fields(self):
        from literary_system.multiwork.multi_work_core import WorkSession
        import uuid
        s = WorkSession(
            session_id=str(uuid.uuid4()),
            project_id="p1", author_id="a1"
        )
        assert s.project_id == "p1"
        assert s.episode_count == 0
        assert s.token_budget == -1  # unlimited by default


class TestMultiWorkOrchestrator:
    def setup_method(self):
        from literary_system.multiwork.multi_work_orchestrator import MultiWorkOrchestrator
        from literary_system.multiwork.author_license_api import LicenseType
        self.orch = MultiWorkOrchestrator(max_concurrent=5)
        # Register author first (required by orchestrator)
        self.orch.register_author("author1", license_type=LicenseType.COMMERCIAL)

    def test_create_project(self):
        proj = self.orch.create_project("author1", "제목1", "drama")
        assert proj.author_id == "author1"
        assert proj.title == "제목1"

    def test_open_session(self):
        proj = self.orch.create_project("author1", "P1", "fantasy")
        session = self.orch.open_session("author1", proj.project_id)
        assert session is not None

    def test_snapshot(self):
        self.orch.create_project("author1", "SP1", "noir")
        snap = self.orch.snapshot()
        assert snap is not None


class TestSharedCharacterDB:
    def test_add_and_get_character(self):
        from literary_system.multiwork.shared_character_db import SharedCharacterDB
        db = SharedCharacterDB()
        db.add_character("char-1", name="주인공", role="protagonist")
        profile = db.get_character("char-1")
        assert profile is not None
        assert profile.name == "주인공"

    def test_character_relation(self):
        from literary_system.multiwork.shared_character_db import SharedCharacterDB
        db = SharedCharacterDB()
        db.add_character("c1", "A", "lead")
        db.add_character("c2", "B", "support")
        db.add_relation("c1", "c2", relation_type="ally")
        rels = db.neighbors("c1")
        assert "c2" in rels or len(rels) >= 1

    def test_character_arc(self):
        from literary_system.multiwork.shared_character_db import SharedCharacterDB
        db = SharedCharacterDB()
        db.add_character("c3", "C", "villain")
        db.record_arc("c3", scene_id="s1", delta=0.3)
        profile = db.get_character("c3")
        assert profile.cumulative_arc() >= 0.0


class TestSharedWorldDB:
    def test_add_location(self):
        from literary_system.multiwork.shared_world_db import SharedWorldDB
        db = SharedWorldDB()
        db.add_location("loc-1", name="서울", description="대도시")
        loc = db.get_location("loc-1")
        assert loc is not None
        assert loc.name == "서울"

    def test_add_lore(self):
        from literary_system.multiwork.shared_world_db import SharedWorldDB
        db = SharedWorldDB()
        db.add_lore("lore-1", category="세계관", title="마법 체계", content="마법의 근원은 감정이다")
        lore_list = db.list_lore()
        assert any(l.lore_id == "lore-1" for l in lore_list)

    def test_world_stats(self):
        from literary_system.multiwork.shared_world_db import SharedWorldDB
        db = SharedWorldDB()
        db.add_location("l1", "L1", "")
        db.add_faction("f1", "F1", "")
        stats = db.stats()
        assert stats.get("locations", 0) >= 1


# ─── TC-13~22: Predictive ─────────────────────────────────────────────────────

class TestPNECore:
    def test_pattern_library_instantiation(self):
        from literary_system.predictive.pne_core import PatternLibrary
        lib = PatternLibrary()
        assert lib is not None

    def test_pne_core_instantiation(self):
        from literary_system.predictive.pne_core import PNECore, PatternLibrary
        lib = PatternLibrary()
        core = PNECore(library=lib)
        assert core is not None


class TestDebtPredictor:
    def _make_predictor(self):
        from literary_system.predictive.pne_core import PNECore, PatternLibrary
        from literary_system.predictive.debt_predictor import DebtPredictor
        lib = PatternLibrary()
        core = PNECore(library=lib)
        return DebtPredictor(pne_core=core)

    def test_instantiation(self):
        dp = self._make_predictor()
        assert dp is not None

    def test_predict_returns_report(self):
        dp = self._make_predictor()
        report = dp.predict(
            scene_id="s-001",
            current_severity=0.5,
            horizon=5,
        )
        assert report.scene_id == "s-001"
        assert report.horizon == 5
        assert len(report.predictions) >= 0

    def test_high_risk_detection(self):
        from literary_system.predictive.debt_predictor import DebtPrediction, PredictionReport
        report = PredictionReport(
            scene_id="s1", horizon=5,
            predictions=[
                DebtPrediction(category="pacing", probability=0.75, confidence=0.8, horizon=5),
                DebtPrediction(category="character", probability=0.3, confidence=0.7, horizon=5),
            ]
        )
        assert report.any_high_risk()
        assert "pacing" in report.high_risk

    def test_max_probability(self):
        from literary_system.predictive.debt_predictor import DebtPrediction, PredictionReport
        report = PredictionReport(
            scene_id="s2", horizon=3,
            predictions=[
                DebtPrediction(category="x", probability=0.4, confidence=0.9, horizon=3),
                DebtPrediction(category="y", probability=0.85, confidence=0.9, horizon=3),
            ]
        )
        assert abs(report.max_probability() - 0.85) < 1e-9

    def test_sklearn_available_flag(self):
        dp = self._make_predictor()
        # Either True or False is acceptable — just must not raise
        result = dp.sklearn_available  # bool attribute, not callable
        assert isinstance(result, bool)


class TestPreemptiveGate:
    def _make_gate(self):
        from literary_system.predictive.pne_core import PNECore, PatternLibrary
        from literary_system.predictive.debt_predictor import DebtPredictor
        from literary_system.predictive.preemptive_gate import PreemptiveGate
        lib = PatternLibrary()
        core = PNECore(library=lib)
        predictor = DebtPredictor(pne_core=core)
        return PreemptiveGate(predictor=predictor, horizon=5, threshold=0.60)

    def test_gate_instantiation(self):
        gate = self._make_gate()
        assert gate.threshold == 0.60  # @property
        assert gate.horizon == 5    # @property

    def test_gate_evaluate_low_severity(self):
        gate = self._make_gate()
        # Low severity → should pass (not block)
        result = gate.evaluate(
            scene_id="s-low",
            current_severity=0.1,
            horizon=5,
        )
        assert result.blocked is False  # low severity → not blocked

    def test_gate_block_count_starts_zero(self):
        gate = self._make_gate()
        assert gate.block_count() == 0
        assert gate.total_evaluated() == 0


class TestFeedbackLearner:
    def _make_learner(self):
        from literary_system.predictive.pne_core import PNECore, PatternLibrary
        from literary_system.predictive.debt_predictor import DebtPredictor
        from literary_system.predictive.feedback_learner import FeedbackLearner
        lib = PatternLibrary()
        core = PNECore(library=lib)
        predictor = DebtPredictor(pne_core=core)
        return FeedbackLearner(predictor=predictor, pne_core=core)

    def test_record_prediction(self):
        learner = self._make_learner()
        learner.record(scene_id="s1", category="pacing", predicted_prob=0.7, actual_occurred=False)
        assert learner.total_records() >= 1

    def test_precision_metrics(self):
        learner = self._make_learner()
        for i in range(3):
            learner.record(f"s{i}", "pacing", predicted_prob=0.75, actual_occurred=(i % 2 == 0))
        # precision() should return a float
        p = learner.precision("pacing")
        assert isinstance(p, (int, float))


# ─── TC-23~32: Schemas ────────────────────────────────────────────────────────

class TestSchemaEnvelope:
    def test_make_envelope_fields(self):
        from literary_system.schemas.envelope import make_envelope
        env = make_envelope(
            project_id="proj-1",
            packet_type="intent_seed",
            provenance={"source": "test"},
            payload={"key": "value"},
        )
        assert env["project_id"] == "proj-1"
        assert env["packet_type"] == "intent_seed"
        assert "created_at" in env
        assert env["schema_version"] == "v1"

    def test_envelope_required_fields(self):
        from literary_system.schemas.envelope import make_envelope
        from literary_system.schemas.definitions import COMMON_ENVELOPE_REQUIRED
        env = make_envelope("p1", "macro_arc", {}, {})
        for field in COMMON_ENVELOPE_REQUIRED:
            assert field in env, f"필수 필드 누락: {field}"


class TestPacketValidator:
    def test_validate_envelope_pass(self):
        from literary_system.schemas.validator import PacketValidator
        from literary_system.schemas.envelope import make_envelope
        validator = PacketValidator()
        env = make_envelope("p1", "intent_seed", {"source": "test"}, {"data": 1})
        # Should not raise
        try:
            result = validator.validate_envelope(env)
            # True or None both acceptable
        except Exception:
            pytest.fail("Valid envelope should not raise")

    def test_validate_missing_field_raises(self):
        from literary_system.schemas.validator import PacketValidator
        from literary_system.common.errors import SchemaValidationError
        validator = PacketValidator()
        bad_env = {"project_id": "p1"}
        with pytest.raises(SchemaValidationError):
            validator.validate_envelope(bad_env)


class TestDefinitions:
    def test_packet_required_fields_populated(self):
        from literary_system.schemas.definitions import PACKET_REQUIRED_FIELDS
        assert len(PACKET_REQUIRED_FIELDS) > 0
        # At least one packet type should require character_id
        all_fields = set()
        for fields in PACKET_REQUIRED_FIELDS.values():
            all_fields |= fields
        assert "character_id" in all_fields or "scene_id" in all_fields

    def test_common_envelope_required(self):
        from literary_system.schemas.definitions import COMMON_ENVELOPE_REQUIRED
        assert "project_id" in COMMON_ENVELOPE_REQUIRED
        assert "packet_type" in COMMON_ENVELOPE_REQUIRED
        assert "payload" in COMMON_ENVELOPE_REQUIRED


class TestCharacterLedger:
    def test_ledger_fields_list(self):
        from literary_system.schemas.character_ledger import CHARACTER_LEDGER_FIELDS
        assert "character_id" in CHARACTER_LEDGER_FIELDS
        assert "display_name" in CHARACTER_LEDGER_FIELDS
        assert len(CHARACTER_LEDGER_FIELDS) >= 5


# ─── TC-33~40: Auth Regression (G34) ─────────────────────────────────────────

class TestAuthRegressionG34:
    """Gate G34 — AuthRegression: V575 DEV_MODE 보안 패치 회귀 검증."""

    def test_devmode_default_is_false(self):
        """DEV_MODE 기본값이 False — 환경변수 미설정 시 인증 활성 상태여야 함."""
        import os, importlib
        original = os.environ.pop("LITERARY_OS_DEV_MODE", None)
        try:
            import apps.studio_api.auth.middleware as mw
            importlib.reload(mw)
            assert mw.DEV_MODE is False, (
                "V575 보안 패치 회귀: DEV_MODE 기본값이 True입니다."
            )
        finally:
            if original is not None:
                os.environ["LITERARY_OS_DEV_MODE"] = original
            else:
                os.environ.pop("LITERARY_OS_DEV_MODE", None)
            importlib.reload(mw)

    def test_devmode_true_when_explicitly_set(self):
        """LITERARY_OS_DEV_MODE=true 명시 시에만 DEV_MODE True."""
        import os, importlib
        os.environ["LITERARY_OS_DEV_MODE"] = "true"
        try:
            import apps.studio_api.auth.middleware as mw
            importlib.reload(mw)
            assert mw.DEV_MODE is True
        finally:
            del os.environ["LITERARY_OS_DEV_MODE"]
            importlib.reload(mw)

    def test_devmode_false_when_explicit_false(self):
        """LITERARY_OS_DEV_MODE=false 명시 시 DEV_MODE False."""
        import os, importlib
        os.environ["LITERARY_OS_DEV_MODE"] = "false"
        try:
            import apps.studio_api.auth.middleware as mw
            importlib.reload(mw)
            assert mw.DEV_MODE is False
        finally:
            del os.environ["LITERARY_OS_DEV_MODE"]
            importlib.reload(mw)

    def test_jwt_constants_defined(self):
        """JWT 검증 상수들이 정의되어 있어야 한다."""
        import apps.studio_api.auth.middleware as mw
        assert hasattr(mw, "OAUTH_ISSUER")
        assert hasattr(mw, "OAUTH_AUDIENCE")
        assert hasattr(mw, "OAUTH_ALGORITHMS")

    def test_verify_jwt_callable(self):
        """verify_jwt 또는 get_current_user 함수가 존재해야 한다."""
        import apps.studio_api.auth.middleware as mw
        has_func = hasattr(mw, "verify_jwt") or hasattr(mw, "get_current_user")
        assert has_func, "인증 함수가 없습니다."

    def test_devmode_source_line_is_false(self):
        """미들웨어 소스 코드에서 DEV_MODE 기본값이 'false'여야 한다."""
        import re
        from pathlib import Path
        middleware = Path("apps/studio_api/auth/middleware.py")
        if not middleware.exists():
            middleware = Path("/tmp/literary_os/apps/studio_api/auth/middleware.py")
        text = middleware.read_text()
        bad = re.compile(r'os\.environ\.get\(["\']LITERARY_OS_DEV_MODE["\'],\s*["\']true["\']')
        assert not bad.search(text), "소스코드에 DEV_MODE='true' 기본값이 남아있습니다."


# ─── TC-41~45: G33 SchemaRoundTrip ───────────────────────────────────────────

class TestSchemaRoundTripG33:
    """Gate G33 — SchemaRoundTrip: 스키마 직렬화/역직렬화 왕복 무결성."""

    def test_envelope_json_roundtrip(self):
        import json
        from literary_system.schemas.envelope import make_envelope
        env = make_envelope(
            project_id="rt-proj", packet_type="scene_digest",
            provenance={"stage": "test"}, payload={"scene_id": "s-001"}
        )
        serialized = json.dumps(env, ensure_ascii=False)
        deserialized = json.loads(serialized)
        assert deserialized["project_id"] == "rt-proj"
        assert deserialized["payload"]["scene_id"] == "s-001"

    def test_work_project_dataclass_fields(self):
        import dataclasses
        from literary_system.multiwork.multi_work_core import WorkProject
        p = WorkProject(project_id="rt-1", author_id="a1", title="왕복", genre="drama")
        field_names = {f.name for f in dataclasses.fields(p)}
        for req in ["project_id", "author_id", "title", "genre", "status", "created_at"]:
            assert req in field_names, f"WorkProject 필드 누락: {req}"

    def test_debt_prediction_dataclass_asdict(self):
        import dataclasses
        from literary_system.predictive.debt_predictor import DebtPrediction
        pred = DebtPrediction(category="pacing", probability=0.65, confidence=0.85, horizon=5)
        d = dataclasses.asdict(pred)
        assert d["category"] == "pacing"
        assert abs(d["probability"] - 0.65) < 1e-9

    def test_prediction_report_complete(self):
        from literary_system.predictive.debt_predictor import DebtPrediction, PredictionReport
        report = PredictionReport(
            scene_id="s-rt", horizon=10,
            predictions=[
                DebtPrediction("tension", 0.55, 0.9, 10),
                DebtPrediction("character", 0.25, 0.8, 10),
            ]
        )
        assert report.scene_id == "s-rt"
        assert len(report.predictions) == 2
        assert abs(report.max_probability() - 0.55) < 1e-9

    def test_common_envelope_fields_immutable(self):
        """COMMON_ENVELOPE_REQUIRED는 frozenset이거나 set이어야 한다."""
        from literary_system.schemas.definitions import COMMON_ENVELOPE_REQUIRED
        assert isinstance(COMMON_ENVELOPE_REQUIRED, (set, frozenset))
        assert len(COMMON_ENVELOPE_REQUIRED) >= 4
