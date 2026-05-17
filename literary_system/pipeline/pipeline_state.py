"""
literary_system/pipeline/pipeline_state.py
==========================================
Literary OS V382 — 파이프라인 실행 추적 시스템

SOVEREIGN_OS V305의 execution_trace / checkpoint 시스템을 Literary OS에 이식.

핵심 원칙:
  "모든 노드는 실행될 때 흔적을 남긴다. 흔적이 없으면 실행되지 않은 것이다."

구성:
  LiteraryPipelineState  — 실행 추적 상태 객체
  append_trace()         — 노드 진입 시 흔적 기록
  save_literary_checkpoint()    — 인메모리 체크포인트 저장
  restore_literary_checkpoint() — 체크포인트 복원
  autosave_literary_state()     — 디스크 자동저장 (장애 복구용)
  run_minimal_pipeline()        — Gate 6 전용 최소 파이프라인 실행기
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, ConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# LiteraryPipelineState — 파이프라인 실행 추적 상태
# ─────────────────────────────────────────────────────────────────────────────

class LiteraryPipelineState(BaseModel):
    """
    파이프라인 실행 중 생성·유지되는 추적 상태.
    모든 오케스트레이터가 공유하여 실행 흔적을 남긴다.

    V382 핵심 추가 필드:
      execution_trace  — 노드별 실행 기록 (append_trace 로 기록)
      checkpoints      — 인메모리 체크포인트 (save_literary_checkpoint 로 저장)
      last_good_node   — 마지막으로 성공한 노드 이름
    """
    # ── 실행 메타 ──────────────────────────────────────────────────────────
    run_id:         str  = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}")
    project_id:     str  = ""
    started_at:     str  = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    out_root:       str  = "./out"

    # ── 실행 추적 (V382 핵심) ─────────────────────────────────────────────
    execution_trace: List[str] = Field(default_factory=list)
    last_good_node:  str       = ""
    checkpoints:     Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    last_disk_checkpoint_path: str = ""

    # ── 파이프라인 산출물 (Gate 검증 후 사용) ────────────────────────────
    seed_contract:   Dict[str, Any] = Field(default_factory=dict)
    arc_node_count:  int  = 0
    budget_episodes: int  = 0
    knowledge_facts: int  = 0
    status:          str  = "running"   # running | completed | failed
    # V383 physics 추적
    physics_trace:   List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")  # 오케스트레이터 확장 필드 허용

    def append_trace(self, gate: str, data: dict) -> None:
        """Gate 7+ 전용 구조화 trace 기록."""
        import datetime as _dt
        entry = {"gate": gate, "ts": _dt.datetime.utcnow().isoformat(), **data}
        self.physics_trace.append(entry)
        fitness_val = data.get('fitness', '?')
        fitness_str = f'{fitness_val:.2f}' if isinstance(fitness_val, float) else str(fitness_val)
        self.execution_trace.append(f'[{gate}] fitness={fitness_str} passed={data.get("passed", "?")}')

    def save_literary_checkpoint(self, name: str) -> None:
        """체크포인트 저장 (physics gate용 래퍼)."""
        import datetime as _dt
        self.checkpoints[name] = {
            "ts": _dt.datetime.utcnow().isoformat(),
            "physics_trace_len": len(self.physics_trace),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 핵심 유틸리티
# ─────────────────────────────────────────────────────────────────────────────

def append_trace(state: LiteraryPipelineState, message: str) -> None:
    """
    파이프라인 노드 실행 흔적 기록.

    SOVEREIGN_OS의 append_trace()를 그대로 이식.
    모든 노드는 진입 시 반드시 이 함수를 호출해야 한다.
    흔적이 없으면 실행되지 않은 것으로 간주한다.
    """
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    entry = f"[{ts}] {message}"
    state.execution_trace.append(entry)
    print(entry)


def save_literary_checkpoint(
    state:     LiteraryPipelineState,
    node_name: str,
    fields:    Optional[List[str]] = None,
) -> None:
    """
    인메모리 체크포인트 저장.

    Args:
        state:     파이프라인 상태
        node_name: 체크포인트 이름 (노드 이름)
        fields:    저장할 필드 목록 (None이면 핵심 필드 자동 선택)
    """
    fields = fields or [
        "run_id", "project_id", "seed_contract",
        "arc_node_count", "budget_episodes", "knowledge_facts",
    ]
    payload: Dict[str, Any] = {}
    for f in fields:
        if hasattr(state, f):
            val = getattr(state, f)
            # 직렬화 가능한 형태로 변환
            if hasattr(val, "model_dump"):
                payload[f] = val.model_dump()
            elif isinstance(val, dict):
                payload[f] = dict(val)
            elif isinstance(val, list):
                payload[f] = list(val)
            else:
                payload[f] = val

    state.checkpoints[node_name] = payload
    state.last_good_node = node_name
    append_trace(state, f"  -> checkpoint saved: {node_name}")


def restore_literary_checkpoint(
    state:     LiteraryPipelineState,
    node_name: str,
) -> bool:
    """
    인메모리 체크포인트에서 상태 복원.

    Returns:
        True  — 복원 성공
        False — 체크포인트 없음
    """
    payload = state.checkpoints.get(node_name)
    if not payload:
        append_trace(state, f"  -> checkpoint missing: {node_name}")
        return False

    for field_name, value in payload.items():
        if hasattr(state, field_name):
            setattr(state, field_name, value)

    append_trace(state, f"  -> checkpoint restored: {node_name}")
    return True


def autosave_literary_state(
    state:  LiteraryPipelineState,
    label:  str,
    status: str = "runtime_checkpoint",
) -> Optional[str]:
    """
    파이프라인 상태를 디스크에 자동 저장.
    프로세스 크래시 시 마지막 상태를 복구할 수 있다.

    Returns:
        저장 경로 (문자열) 또는 None (저장 실패 시)
    """
    try:
        backup_dir = Path(state.out_root) / "sessions" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        payload = state.model_dump()
        payload["status"]           = status
        payload["updated_at"]       = datetime.now(timezone.utc).isoformat()
        payload["checkpoint_label"] = label

        path = backup_dir / f"{state.run_id}_{label}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        state.last_disk_checkpoint_path = str(path)
        append_trace(state, f"  -> disk autosave: {path.name}")
        return str(path)

    except Exception as exc:
        append_trace(state, f"  -> disk autosave failed [{label}]: {exc}")
        return None


def prune_trace(state: LiteraryPipelineState, keep: int = 120) -> None:
    """trace가 너무 길어지면 최근 N개만 유지."""
    if len(state.execution_trace) > keep:
        state.execution_trace = state.execution_trace[-keep:]


# ─────────────────────────────────────────────────────────────────────────────
# run_minimal_pipeline — Gate 6 전용 핵심 로직 생존 검증기
# ─────────────────────────────────────────────────────────────────────────────

def run_minimal_pipeline(
    seed_text: str = "테스트 씨드 — 형사가 의뢰인을 보호하다 의심한다",
    episodes:  int = 4,
    out_root:  str = "./out",
) -> LiteraryPipelineState:
    """
    Gate 6(pipeline_survival) 전용 최소 파이프라인 실행기.

    모든 핵심 모듈을 순서대로 호출하고 execution_trace에 기록한다.
    Gate는 이 trace를 검사하여 각 모듈이 실제 실행됐는지 확인한다.

    실행 순서 (SOVEREIGN_OS 파이프라인 순서 준수):
      Node_SeedCompiler
      → Node_SeriesArcPlanner
      → Node_CausalPlotGraph
      → Node_EpisodeRevealBudget
      → Node_KnowledgeStateTracker
      → Node_CharacterKnowledgeProseBridge

    Returns:
        LiteraryPipelineState — execution_trace 포함
    """
    state = LiteraryPipelineState(out_root=out_root)

    append_trace(state,
        f"\n[Pipeline] Literary OS V382 최소 파이프라인 시작"
        f" | seed='{seed_text[:40]}' | episodes={episodes}"
        f" | run_id={state.run_id}"
    )

    # ── Node 1: SeedCompiler ──────────────────────────────────────────────
    append_trace(state, "\n[Node_SeedCompiler] compile 시작")
    try:
        from literary_system.compiler.seed_compiler import SeedCompiler
        seed = SeedCompiler().compile(seed_text)
        state.seed_contract = seed
        state.project_id    = seed.get("project_id", state.run_id)
        append_trace(state, f"  -> 씨드 컴파일 완료 | project_id={state.project_id}")
        save_literary_checkpoint(state, "seed_compiler", ["run_id", "project_id", "seed_contract"])
        autosave_literary_state(state, "node_seed_compiler", out_root=out_root)
    except Exception as exc:
        append_trace(state, f"  -> SeedCompiler 실패: {exc}")

    # ── Node 2: SeriesArcPlanner ──────────────────────────────────────────
    append_trace(state, "\n[Node_SeriesArcPlanner] plan() 실행")
    try:
        from literary_system.arc import SeriesArcPlanner
        planner = SeriesArcPlanner(
            total_episodes=max(episodes * 2, 8),
            series_title=state.project_id or "gate_test",
        )
        graph = planner.plan()
        nodes = list(graph._nodes.values())
        state.arc_node_count = len(nodes)
        append_trace(state, f"  -> 아크 플랜 완료 | nodes={state.arc_node_count}")
        save_literary_checkpoint(state, "series_arc_planner", ["run_id", "arc_node_count"])
        autosave_literary_state(state, "node_series_arc_planner", out_root=out_root)
    except Exception as exc:
        append_trace(state, f"  -> SeriesArcPlanner 실패: {exc}")

    # ── Node 3: CausalPlotGraph ───────────────────────────────────────────
    append_trace(state, "\n[Node_CausalPlotGraph] 인과율 그래프 초기화")
    try:
        from literary_system.arc import ArcPlotNode, ArcAct, CausalPlotGraph
        cpg = CausalPlotGraph()
        root_node = ArcPlotNode(
            episode_id="ep_root", episode_index=1,
            title="발단 씨드", act=ArcAct.GI,
        )
        cpg.add_node(root_node)
        append_trace(state, f"  -> 인과 그래프 초기화 완료 | nodes={len(cpg._nodes)}")
        save_literary_checkpoint(state, "causal_plot_graph", ["run_id"])
        autosave_literary_state(state, "node_causal_plot_graph", out_root=out_root)
    except Exception as exc:
        append_trace(state, f"  -> CausalPlotGraph 실패: {exc}")

    # ── Node 4: EpisodeRevealBudget ───────────────────────────────────────
    append_trace(state, "\n[Node_EpisodeRevealBudget] 공개 예산 설정")
    try:
        from literary_system.ledgers.episode_reveal_budget import (
            EpisodeRevealBudget, RevealPolicy,
        )
        budget = EpisodeRevealBudget()
        for ep in range(1, episodes + 1):
            budget.set_policy(f"ep_{ep}", "core_secret", RevealPolicy.BLOCK)
            budget.set_policy(f"ep_{ep}", "foreshadow_hint", RevealPolicy.FORESHADOW_ONLY)
        state.budget_episodes = episodes
        append_trace(state, f"  -> {episodes}화 예산 정책 설정 완료")
        save_literary_checkpoint(state, "episode_reveal_budget", ["run_id", "budget_episodes"])
        autosave_literary_state(state, "node_episode_reveal_budget", out_root=out_root)
    except Exception as exc:
        append_trace(state, f"  -> EpisodeRevealBudget 실패: {exc}")

    # ── Node 5: KnowledgeStateTracker ─────────────────────────────────────
    append_trace(state, "\n[Node_KnowledgeStateTracker] 지식 상태 초기화")
    try:
        from literary_system.world.knowledge_state_tracker import (
            KnowledgeStateTracker, KnowledgeStatus,
        )
        tracker = KnowledgeStateTracker(project_id=state.project_id or "gate_test")
        tracker.register_fact(
            fact_id="root_secret", fact_type="identity",
            description="핵심 서사 비밀", true_value="진실은 숨겨진다",
            reader_knows=False,
        )
        tracker.set_knowledge("lead_char", "root_secret", KnowledgeStatus.UNAWARE, episode_no=1)
        state.knowledge_facts = 1
        append_trace(state, f"  -> 지식 상태 초기화 완료 | facts={state.knowledge_facts}")
        save_literary_checkpoint(state, "knowledge_state_tracker", ["run_id", "knowledge_facts"])
        autosave_literary_state(state, "node_knowledge_state_tracker", out_root=out_root)
        # tracker를 state에 임시 저장 (다음 노드용)
        state.__dict__["_tracker"] = tracker
    except Exception as exc:
        append_trace(state, f"  -> KnowledgeStateTracker 실패: {exc}")

    # ── Node 6: CharacterKnowledgeProseBridge ─────────────────────────────
    append_trace(state, "\n[Node_CharacterKnowledgeProseBridge] 산문 브릿지 연결")
    try:
        from literary_system.world.character_knowledge_prose_bridge import (
            CharacterKnowledgeProseBridge,
        )
        tracker = state.__dict__.get("_tracker")
        if tracker is None:
            from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker
            tracker = KnowledgeStateTracker(project_id=state.project_id or "gate_test")
        bridge = CharacterKnowledgeProseBridge(tracker=tracker)
        append_trace(state, "  -> 산문 브릿지 연결 완료")
        save_literary_checkpoint(state, "character_knowledge_prose_bridge", ["run_id"])
        autosave_literary_state(state, "node_character_knowledge_prose_bridge", out_root=out_root)
    except Exception as exc:
        append_trace(state, f"  -> CharacterKnowledgeProseBridge 실패: {exc}")

    # ── 완료 ─────────────────────────────────────────────────────────────
    state.status = "completed"
    append_trace(state,
        f"\n[Pipeline] 완료"
        f" | executed_nodes={len(state.checkpoints)}"
        f" | trace_entries={len(state.execution_trace)}"
    )
    autosave_literary_state(state, "pipeline_completed", status="completed", out_root=out_root)
    prune_trace(state, keep=200)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# autosave 시그니처 오버로드 (out_root 인자 지원)
# ─────────────────────────────────────────────────────────────────────────────

def autosave_literary_state(  # noqa: F811  (재정의)
    state:    LiteraryPipelineState,
    label:    str,
    status:   str = "runtime_checkpoint",
    out_root: Optional[str] = None,
) -> Optional[str]:
    """
    파이프라인 상태를 디스크에 자동 저장 (out_root 오버라이드 지원).
    """
    effective_root = out_root or state.out_root
    try:
        backup_dir = Path(effective_root) / "sessions" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        payload = state.model_dump()
        payload["status"]           = status
        payload["updated_at"]       = datetime.now(timezone.utc).isoformat()
        payload["checkpoint_label"] = label

        path = backup_dir / f"{state.run_id}_{label}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        state.last_disk_checkpoint_path = str(path)
        append_trace(state, f"  -> disk autosave: {path.name}")
        return str(path)

    except Exception as exc:
        append_trace(state, f"  -> disk autosave failed [{label}]: {exc}")
        return None
