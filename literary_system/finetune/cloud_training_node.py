"""
finetune/cloud_training_node.py — 클라우드 실측 학습 노드 마무리 (V786, ADR-247).

T1 런북 ②~③의 클라우드판: 선호쌍 → (비공개 암호화 업로드) → RunPod QLoRA DPO →
LoRA 어댑터 회수 → 업로드 데이터 자동삭제 → ΔW 산출 → G_LOOPC_WINRATE 수용판정.
"실측하여 학습하는 노드"의 마무리.

회사 PC=노트북 약GPU → 이 클라우드 노드가 학습을 담당(집=4070 로컬 노드와 대칭).
저작권 안전: 올리는 건 비공개·암호화·임시, 회수는 verbatim 없는 어댑터, 끝나면 즉시 삭제.
LLM-0: 오케스트레이션 결정론.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.finetune.cloud_storage import CloudStore
from literary_system.finetune.runpod_lifecycle import RunPodJobLifecycle


@dataclass
class CloudNodeReport:
    status:        str                 # "completed" | "failed" | "planned"
    dataset_url:   str
    artifact_path: str
    deleted:       int                 # 자동삭제된 임시 객체 수
    lifecycle:     Dict[str, Any]
    w0:            Optional[float] = None
    w1:            Optional[float] = None
    gate:          Optional[Dict[str, Any]] = None

    @property
    def delta_w(self) -> Optional[float]:
        if self.w0 is None or self.w1 is None:
            return None
        return round(self.w1 - self.w0, 4)

    def summary(self) -> str:
        dw = self.delta_w
        return (f"CloudNode[{self.status}] artifact={self.artifact_path or '-'} "
                f"삭제={self.deleted} ΔW={dw if dw is not None else 'pending'}")

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "dataset_url": self.dataset_url,
                "artifact_path": self.artifact_path, "deleted": self.deleted,
                "lifecycle": self.lifecycle, "w0": self.w0, "w1": self.w1,
                "delta_w": self.delta_w, "gate": self.gate, "summary": self.summary()}


class CloudTrainingNode:
    """클라우드 학습 노드: 비공개 저장 + RunPod 학습 + 회수 + 자동삭제 + ΔW/수용판정."""

    def __init__(self, adapter, store: CloudStore, max_polls: int = 20) -> None:
        self._adapter = adapter
        self._store = store
        self._lifecycle = RunPodJobLifecycle(
            adapter, uploader=store.put, downloader=store.get, max_polls=max_polls)

    def run(self, dpo_pairs_path: str, model_name: str, *, hours: float = 2.0,
            dry_run: bool = True, w0: Optional[float] = None,
            measured_w1: Optional[float] = None, kl: float = 0.0,
            artifact_dest: str = "./lora_out_cloud",
            target_w: float = 0.60) -> CloudNodeReport:
        # ①~④ 라이프사이클: (store.put로 암호화 업로드) → 학습 → (store.get로 회수)
        # output_url은 store가 어댑터 회수용 프리사인 URL을 제공(여기선 lifecycle 내 다운로더 사용)
        # 어댑터 회수용 GET URL(store가 제공). pod는 대응 PUT URL로 어댑터 업로드.
        out_url = ""
        if not dry_run and hasattr(self._store, "url_for"):
            out_url = self._store.url_for("litos-private/adapter", "get")
        rep = self._lifecycle.run(dpo_pairs_path, model_name, hours=hours,
                                  output_url=out_url,
                                  dry_run=dry_run, artifact_dest=artifact_dest)
        # ⑤ 자동삭제(저작권 안전) — 업로드한 임시 비공개 데이터 제거
        deleted = 0
        if hasattr(self._store, "cleanup"):
            deleted = self._store.cleanup()

        # ⑥ ΔW 수용판정(실측 W₁ 제공 시 G_LOOPC_WINRATE)
        gate = None
        if w0 is not None and measured_w1 is not None:
            from literary_system.learning.winrate_gate import g_loopc_winrate
            g = g_loopc_winrate(w0, measured_w1, kl=kl)
            gate = g.to_dict()

        return CloudNodeReport(
            status=rep.status, dataset_url=rep.dataset_url, artifact_path=rep.artifact_path,
            deleted=deleted, lifecycle=rep.to_dict(), w0=w0, w1=measured_w1, gate=gate)
