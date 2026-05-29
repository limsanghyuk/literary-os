"""NarrativeConductor — V408.

얇은 오케스트레이터 (thin orchestrator pattern, 3인 합의).
비즈니스 로직 없음 — NarrativeMemory 기반 시리즈 생성 진행 위임만 담당.

설계 원칙:
  - start_series()   : 메모리 초기화 + ep000 저장
  - write_episode()  : 메모리 로드 → 씬 파이프라인 위임 → 메모리 저장
  - validate_series(): 시리즈 전체 LongformEndurance 검증
  - get_snapshot()   : 최신 상태 SeriesSnapshot 반환
  - LLM 0회
  - 모든 핵심 노드에 append_trace() 의무
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.episode.episode_state import NarrativeStateTensor, SeriesConfig
from literary_system.memory.narrative_memory_store import (
    EpisodeMemory,
    EpisodeMemoryNotFound,
    NarrativeMemoryStore,
    SeriesNotFound,
)
from literary_system.physics.coefficient_store import PhysicsCoefficientStore

# ── 데이터 구조 ───────────────────────────────────────────────────────────────

@dataclass
class SeriesSnapshot:
    """NarrativeMemory에서 복원된 시리즈 전체 상태 (설계도 G)."""
    series_id: str
    last_episode: int                    # 마지막으로 완료된 에피소드 인덱스
    pipeline_state: Dict[str, Any]       # LiteraryPipelineState 직렬화
    nkg: Optional[Any]                   # NKGGraphStore 인스턴스 (로드된 경우)
    debt_ledger: Dict[str, Any]          # PayoffDebtLedger 직렬화
    coefficient_store: PhysicsCoefficientStore
    trajectory: Dict[str, float]         # {SP, RU, ET, RD}
    execution_trace: List[str] = field(default_factory=list)

    def add_trace(self, msg: str) -> None:
        self.execution_trace.append(msg)

    @property
    def next_episode(self) -> int:
        return self.last_episode + 1


@dataclass
class EpisodeResult:
    """write_episode() 반환값."""
    series_id: str
    episode_idx: int
    memory_path: str = ""                 # 저장된 JSON 경로
    execution_trace: List[str] = field(default_factory=list)
    gate_passed: bool = True
    overall_pass: bool = True

    def add_trace(self, msg: str) -> None:
        self.execution_trace.append(msg)


# ── NarrativeConductor ────────────────────────────────────────────────────────

class NarrativeConductor:
    """V408 — NarrativeMemory 기반 시리즈 생성 진행 오케스트레이터.

    모든 상태는 NarrativeMemoryStore에서 로드/저장.
    오케스트레이터 자체는 상태를 보유하지 않는다 (stateless).
    """

    def __init__(
        self,
        memory_root: Optional[str] = None,
        coefficient_store: Optional[PhysicsCoefficientStore] = None,
    ) -> None:
        self._memory = NarrativeMemoryStore(memory_root=memory_root)
        self._default_coefficients = coefficient_store or PhysicsCoefficientStore()

    # ── 시리즈 시작 ───────────────────────────────────────────────────────────

    def start_series(
        self,
        series_config: SeriesConfig,
        series_id: str,
        seed_metadata: Optional[dict] = None,
    ) -> SeriesSnapshot:
        """시리즈 초기화 + ep000(초기 상태) 저장.

        Args:
            series_config: SeriesConfig (title, total_episodes 등)
            series_id: 고유 시리즈 식별자 ("my_drama_2026" 등)
            seed_metadata: 추가 메타데이터 (선택)

        Returns:
            SeriesSnapshot (last_episode=0)
        """
        trace: List[str] = []
        trace.append(f"NarrativeConductor.start_series: series_id={series_id}")

        # 시리즈 디렉토리 초기화
        metadata = {
            "series_id": series_id,
            "title": series_config.title,
            "total_episodes": series_config.total_episodes,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        if seed_metadata:
            metadata.update(seed_metadata)
        self._memory.init_series(series_id, metadata)
        trace.append(f"  -> NarrativeMemory initialized: series_id={series_id}")

        # 초기 상태 ep000 저장
        initial_coefficients = self._default_coefficients
        ep0 = EpisodeMemory(
            series_id=series_id,
            episode_idx=0,
            created_at=datetime.datetime.utcnow().isoformat(),
            pipeline_state={
                "series_title": series_config.title,
                "total_episodes": series_config.total_episodes,
            },
            narrative_tensor={"SP": 0.3, "RU": 0.0, "ET": 0.0, "RD": 1.0},
            nkg_snapshot_path="",
            debt_ledger_snapshot={"open": [], "paid": [], "defaulted": []},
            coefficient_snapshot=initial_coefficients.as_dict(),
        )
        saved_path = self._memory.save_episode(ep0)
        trace.append(f"  -> ep000 saved: {saved_path}")

        snapshot = SeriesSnapshot(
            series_id=series_id,
            last_episode=0,
            pipeline_state=ep0.pipeline_state,
            nkg=None,
            debt_ledger=ep0.debt_ledger_snapshot,
            coefficient_store=initial_coefficients,
            trajectory=ep0.narrative_tensor,
            execution_trace=trace,
        )
        return snapshot

    # ── 에피소드 작성 ──────────────────────────────────────────────────────────

    def write_episode(
        self,
        series_id: str,
        episode_n: int,
        scene_outputs: Optional[List[dict]] = None,
    ) -> EpisodeResult:
        """에피소드 n 작성 → 메모리 저장.

        실제 씬 생성은 FullSceneOrchestrator에 위임(외부).
        이 메서드는 메모리 로드/저장과 상태 업데이트만 담당.

        Args:
            series_id: 시리즈 ID
            episode_n: 작성할 에피소드 번호 (1 이상)
            scene_outputs: 씬 파이프라인 결과 (없으면 빈 에피소드)

        Returns:
            EpisodeResult
        """
        result = EpisodeResult(series_id=series_id, episode_idx=episode_n)
        result.add_trace(
            f"NarrativeConductor.write_episode: series_id={series_id} ep={episode_n}"
        )

        # [1] 이전 상태 로드
        prev_memory = self._memory.get_latest_episode(series_id)
        if prev_memory is None:
            raise SeriesNotFound(
                f"Series '{series_id}' not initialized. Call start_series() first."
            )
        result.add_trace(
            f"  -> prev_episode loaded: ep{prev_memory.episode_idx:03d}"
        )

        # [2] 계수 복원
        coeff = PhysicsCoefficientStore()
        coeff.update(**prev_memory.coefficient_snapshot)

        # [3] 궤도 업데이트 (씬 결과 반영 또는 기본 진행)
        prev_tensor = prev_memory.narrative_tensor
        progress = episode_n / max(
            prev_memory.pipeline_state.get("total_episodes", 16), 1
        )
        new_tensor = _advance_tensor(prev_tensor, progress, scene_outputs)
        result.add_trace(
            f"  -> narrative_tensor updated: SP={new_tensor['SP']:.3f} "
            f"RU={new_tensor['RU']:.3f} ET={new_tensor['ET']:.3f} RD={new_tensor['RD']:.3f}"
        )

        # [4] 부채 원장 업데이트 (씬 결과 기반, 간략)
        debt_snapshot = _update_debt(prev_memory.debt_ledger_snapshot, scene_outputs)

        # [5] 에피소드 메모리 저장
        ep_mem = EpisodeMemory(
            series_id=series_id,
            episode_idx=episode_n,
            created_at=datetime.datetime.utcnow().isoformat(),
            pipeline_state={
                **prev_memory.pipeline_state,
                "last_written_episode": episode_n,
            },
            narrative_tensor=new_tensor,
            nkg_snapshot_path="",
            debt_ledger_snapshot=debt_snapshot,
            coefficient_snapshot=coeff.as_dict(),
        )
        saved_path = self._memory.save_episode(ep_mem)
        result.memory_path = saved_path
        result.add_trace(f"  -> ep{episode_n:03d} saved: {saved_path}")

        return result

    # ── 시리즈 검증 ───────────────────────────────────────────────────────────

    def validate_series(self, series_id: str):
        """시리즈 전체 LongformEndurance 검증 → EnduranceRunReport.

        NarrativeMemory에서 시리즈 데이터를 로드하여
        LongformEnduranceOrchestrator에 위임.
        """
        from literary_system.orchestrators.longform_endurance_orchestrator import (
            LongformEnduranceOrchestrator,
            LongformInput,
        )

        memories = self._memory.load_series(series_id)
        metadata = self._memory.get_series_metadata(series_id)

        cfg = SeriesConfig(
            title=metadata.get("title", series_id),
            total_episodes=metadata.get("total_episodes", 16),
        )
        # NarrativeStateTensor — 마지막 저장값 복원
        last_tensor = memories[-1].narrative_tensor if memories else {}
        tensor = NarrativeStateTensor(
            SP=last_tensor.get("SP", 0.5),
            RU=last_tensor.get("RU", 0.3),
            ET=last_tensor.get("ET", 0.0),
            RD=last_tensor.get("RD", 0.8),
        )
        inp = LongformInput(series_config=cfg, narrative_state=tensor)
        orchestrator = LongformEnduranceOrchestrator()
        return orchestrator.run(inp)

    # ── 스냅샷 조회 ───────────────────────────────────────────────────────────

    def get_snapshot(self, series_id: str) -> SeriesSnapshot:
        """현재 시리즈 상태를 SeriesSnapshot으로 반환."""
        latest = self._memory.get_latest_episode(series_id)
        if latest is None:
            raise SeriesNotFound(f"Series '{series_id}' not found or empty")

        coeff = PhysicsCoefficientStore()
        coeff.update(**latest.coefficient_snapshot)

        nkg = None
        if latest.nkg_snapshot_path:
            nkg = self._memory.load_nkg(series_id, latest.episode_idx)

        return SeriesSnapshot(
            series_id=series_id,
            last_episode=latest.episode_idx,
            pipeline_state=latest.pipeline_state,
            nkg=nkg,
            debt_ledger=latest.debt_ledger_snapshot,
            coefficient_store=coeff,
            trajectory=latest.narrative_tensor,
        )


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _advance_tensor(
    prev: dict, progress: float, scene_outputs: Optional[List[dict]]
) -> Dict[str, float]:
    """이전 궤도 텐서에서 다음 에피소드 텐서 계산 (결정론적, LLM 0).

    SP(씬 압력): 진행률에 따라 상승
    RU(미해결 잔여): 씬 결과 기반
    ET(감정 궤도): 중간 이후 양전환
    RD(관계 감쇠): 에피소드 진행에 따라 서서히 감소
    """
    sp = min(1.0, prev.get("SP", 0.3) + 0.05 * (1 + progress))
    ru = min(1.0, prev.get("RU", 0.0) + 0.03)
    et = prev.get("ET", 0.0) + (0.05 if progress >= 0.5 else -0.02)
    et = max(-1.0, min(1.0, et))
    rd = max(0.0, prev.get("RD", 1.0) - 0.02)

    if scene_outputs:
        resolved = sum(1 for s in scene_outputs if s.get("residue_resolved", False))
        ru = max(0.0, ru - resolved * 0.05)

    return {
        "SP": round(sp, 4),
        "RU": round(ru, 4),
        "ET": round(et, 4),
        "RD": round(rd, 4),
    }


def _update_debt(
    prev_debt: dict, scene_outputs: Optional[List[dict]]
) -> Dict[str, Any]:
    """부채 원장 업데이트 (간략 — 전체 구현은 PayoffDebtLedger에 위임)."""
    debt = {
        "open": list(prev_debt.get("open", [])),
        "paid": list(prev_debt.get("paid", [])),
        "defaulted": list(prev_debt.get("defaulted", [])),
    }
    if scene_outputs:
        for s in scene_outputs:
            for paid_id in s.get("paid_foreshadowings", []):
                if paid_id in debt["open"]:
                    debt["open"].remove(paid_id)
                    debt["paid"].append(paid_id)
            for new_id in s.get("new_foreshadowings", []):
                debt["open"].append(new_id)
    return debt
