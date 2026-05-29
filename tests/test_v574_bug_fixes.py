"""
V574 Bug Fix 검증 테스트
========================
Bug-1: AutoRepairExecutor — SceneChangePreGate에 NarrativeImpactAnalyzer 대신 NarrativeGraphStore 전달
Bug-2: Studio API analyze.py — FastAPI 미설치 환경에서 raise ImportError 제거, stub router 사용
Bug-3: knowledge_access 타입 불일치 — V573 코드베이스에 해당 필드 미존재 (V571-dev 환경 한정 이슈)
"""
from __future__ import annotations
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Bug-1: AutoRepairExecutor 의존성 역전 수정
# ─────────────────────────────────────────────────────────────────────────────
class TestBug1AutoRepairExecutor:
    """
    Bug-1 (CRITICAL): AutoRepairExecutor.__init__ 내부에서
    SceneChangePreGate(analyzer) → SceneChangePreGate(store) 수정.
    SceneChangePreGate는 내부적으로 NarrativeImpactAnalyzer를 직접 생성해야 한다.
    """

    def test_auto_repair_executor_instantiation(self):
        """AutoRepairExecutor가 NarrativeGraphStore로 정상 생성되는지 확인"""
        from literary_system.graph_intelligence.asd.auto_repair_executor import AutoRepairExecutor
        from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
        from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph

        store = NarrativeGraphStore()
        cdg = CodeDependencyGraph()
        cdg.build()
        executor = AutoRepairExecutor(store, cdg)
        assert executor is not None

    def test_gate26_receives_narrative_graph_store(self):
        """AutoRepairExecutor 내부 Gate26이 NarrativeGraphStore를 보유하는지 확인"""
        from literary_system.graph_intelligence.asd.auto_repair_executor import AutoRepairExecutor
        from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
        from literary_system.graph_intelligence.scene_change_pre_gate import SceneChangePreGate
        from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph

        store = NarrativeGraphStore()
        cdg = CodeDependencyGraph()
        cdg.build()
        executor = AutoRepairExecutor(store, cdg)

        gate26 = executor._protocol._gate26
        assert isinstance(gate26, SceneChangePreGate), \
            f"gate26은 SceneChangePreGate여야 함, 실제: {type(gate26).__name__}"
        assert isinstance(gate26._store, NarrativeGraphStore), \
            f"gate26._store는 NarrativeGraphStore여야 함, 실제: {type(gate26._store).__name__}"

    def test_narrative_impact_analyzer_not_passed_as_store(self):
        """NarrativeImpactAnalyzer가 store 자리에 전달되지 않는지 확인"""
        from literary_system.graph_intelligence.asd.auto_repair_executor import AutoRepairExecutor
        from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
        from literary_system.graph_intelligence.narrative_impact_analyzer import NarrativeImpactAnalyzer
        from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph

        store = NarrativeGraphStore()
        cdg = CodeDependencyGraph()
        cdg.build()
        executor = AutoRepairExecutor(store, cdg)

        gate26 = executor._protocol._gate26
        # gate26._store가 NarrativeImpactAnalyzer가 아니어야 함 (Bug-1의 근본 원인)
        assert not isinstance(gate26._store, NarrativeImpactAnalyzer), \
            "Bug-1 재발: gate26._store에 NarrativeImpactAnalyzer가 전달됨"

    def test_dry_run_execution_no_error(self):
        """repair_fn=None (dry_run) 모드에서 ExecutionStatus.ERROR가 발생하지 않는지 확인"""
        from literary_system.graph_intelligence.asd.auto_repair_executor import (
            AutoRepairExecutor, ExecutionStatus
        )
        from literary_system.graph_intelligence.asd.story_doctor_orchestrator import (
            RepairCategory, RepairRecommendation
        )
        from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
        from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph

        store = NarrativeGraphStore()
        cdg = CodeDependencyGraph()
        cdg.build()
        executor = AutoRepairExecutor(store, cdg, repair_fn=None)

        rec = RepairRecommendation(
            recommendation_id="rec-001",
            node_id="scene_01",
            category=RepairCategory.RESOLVE_SECRET,
            label="test repair",
            priority_score=0.8,
            blast_ratio=0.3,
            severity=0.8,
            detail="test repair detail",
        )
        result = executor.execute(rec)
        # Bug-1 수정 전: store 자리에 analyzer가 들어가 get_node() 호출 시 AttributeError → ERROR
        # Bug-1 수정 후: DRY_RUN 또는 GATE_FAIL (씬이 없으면 gate 통과 안 할 수 있음), 절대 ERROR 아님
        assert result.status != ExecutionStatus.ERROR, \
            f"Bug-1 재발: ExecutionStatus.ERROR 발생. message={result.error_message}"


# ─────────────────────────────────────────────────────────────────────────────
# Bug-2: analyze.py FastAPI 환경 의존 수정
# ─────────────────────────────────────────────────────────────────────────────
class TestBug2StudioApiAnalyze:
    """
    Bug-2 (환경 의존): FastAPI 미설치 환경에서 analyze.py import 시
    raise ImportError 대신 stub router를 사용해 모듈 로드 성공해야 함.
    """

    def test_analyze_module_importable(self):
        """analyze.py가 ImportError 없이 import 가능한지 확인"""
        try:
            from apps.studio_api.routers import analyze  # noqa: F401
            assert True
        except ImportError as e:
            pytest.fail(f"Bug-2 재발: analyze.py import 시 ImportError 발생: {e}")

    def test_router_object_exists(self):
        """router 객체가 None이 아닌 유효한 객체로 존재하는지 확인"""
        from apps.studio_api.routers.analyze import router
        assert router is not None, "router 객체가 None"

    def test_router_has_post_and_get(self):
        """router가 post/get 속성을 가지는지 확인 (stub 또는 실제 APIRouter 모두)"""
        from apps.studio_api.routers.analyze import router
        assert hasattr(router, 'post'), "router에 post 속성 없음"
        assert hasattr(router, 'get'), "router에 get 속성 없음"


# ─────────────────────────────────────────────────────────────────────────────
# Bug-3: knowledge_access (V573 코드베이스 범위 확인)
# ─────────────────────────────────────────────────────────────────────────────
class TestBug3KnowledgeAccessScope:
    """
    Bug-3 (타입 안전성): knowledge_access 타입 불일치는 회사PC가 테스트한
    V571 (v557_dev) 환경에서 발견된 이슈로, V573 literary_system/ 내에는
    해당 필드가 존재하지 않음을 확인한다.
    """

    def test_knowledge_access_not_in_literary_system(self):
        """literary_system/ 내 CharacterSeed.knowledge_access 필드 미존재 확인"""
        import os, re
        pattern = re.compile(r'knowledge_access')
        found = []
        for root, _, files in os.walk('literary_system'):
            for f in files:
                if f.endswith('.py') and '__pycache__' not in root:
                    path = os.path.join(root, f)
                    if pattern.search(open(path).read()):
                        found.append(path)
        # V573 literary_system/에는 knowledge_access 필드가 없어야 함
        assert not found, \
            f"Bug-3 해당 필드 발견 (수동 타입 검증 필요): {found}"
