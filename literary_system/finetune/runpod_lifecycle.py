"""
finetune/runpod_lifecycle.py — RunPod 학습 운영 라이프사이클 (V777, ADR-237).

V772 어댑터는 파드 생성만 했다. 실 학습은 데이터가 파드에 가야 하고 결과가 돌아와야 한다.
본 모듈: ①데이터셋 업로드 → ②파드 학습 기동 → ③폴링(완료 대기) → ④LoRA 어댑터 회수 → ⑤등재.
업로더/다운로더는 주입(HF Hub·S3·B2 등) → 테스트는 fake, 운영은 실 스토리지. 자격증명 없이도 계획 가능.
보안: 키·URL 토큰은 직렬화 미포함. dry_run/키없음=계획만(업로드·폴링 미수행).
LLM-0: GPU 인프라 운영(LLM 미호출).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from literary_system.finetune.gpu_adapter import GPUJobRequest, GPUJobStatus

Uploader = Callable[[str], str]            # local_path -> remote_url
Downloader = Callable[[str, str], bool]    # (remote_url, dest_path) -> ok

TERMINAL = {"EXITED", "COMPLETED", "TERMINATED", "STOPPED", "FAILED"}


@dataclass
class LifecycleStage:
    name:   str
    status: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass
class LifecycleReport:
    status:        str                 # "planned" | "running" | "completed" | "failed"
    pod_id:        str
    dataset_url:   str
    artifact_path: str
    stages:        List[LifecycleStage] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (f"RunPod-Lifecycle[{self.status}] pod={self.pod_id or '-'} "
                f"stages={len(self.stages)} artifact={self.artifact_path or '-'}")

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "pod_id": self.pod_id, "dataset_url": self.dataset_url,
                "artifact_path": self.artifact_path, "stages": [s.to_dict() for s in self.stages],
                "summary": self.summary}


class RunPodJobLifecycle:
    """업로드→학습→폴링→회수 전 주기 오케스트레이션."""

    def __init__(self, adapter, uploader: Optional[Uploader] = None,
                 downloader: Optional[Downloader] = None, max_polls: int = 20,
                 registry=None) -> None:
        self._a = adapter
        self._up = uploader
        self._down = downloader
        self._max_polls = max_polls
        self._registry = registry

    def _has_key(self) -> bool:
        return bool(getattr(self._a, "_api_key", ""))

    def run(self, dataset_path: str, model_name: str, hours: float = 2.0,
            output_url: str = "", dry_run: bool = True,
            artifact_dest: str = "./lora_out") -> LifecycleReport:
        stages: List[LifecycleStage] = []

        # 계획 모드(dry_run 또는 키없음): 업로드/폴링/회수 미수행
        if dry_run or not self._has_key():
            stages.append(LifecycleStage("plan", "ok",
                          "dry_run/키없음 → 업로드·폴링·회수 미수행(계획만). 실행=dry_run=False+키+업로더/다운로더"))
            return LifecycleReport("planned", "", "", "", stages)

        # ① 업로드
        if self._up is None:
            stages.append(LifecycleStage("upload", "skipped", "업로더 미주입 → DATASET 경로 직접 사용"))
            dataset_url = ""
        else:
            dataset_url = self._up(dataset_path)
            stages.append(LifecycleStage("upload", "ok", "dataset → 원격 URL 확보"))

        # ② 파드 학습 기동
        req = GPUJobRequest(model_name=model_name, dataset_path=dataset_path,
                            hours_estimate=hours, dry_run=False,
                            extra={"dataset_url": dataset_url, "output_url": output_url, "objective": "dpo"})
        res = self._a.launch_job(req)
        pod_id = res.metadata.get("pod_id", "") if res.metadata else ""
        if res.status == GPUJobStatus.FAILED:
            stages.append(LifecycleStage("launch", "failed", res.error))
            return LifecycleReport("failed", pod_id, dataset_url, "", stages)
        stages.append(LifecycleStage("launch", "ok", f"pod={pod_id}"))

        # ③ 폴링(완료 대기, 유한)
        terminal = None
        for i in range(self._max_polls):
            st = self._a.poll(pod_id)
            cur = (st.get("desiredStatus") or st.get("status") or "").upper()
            if cur in TERMINAL:
                terminal = cur; break
        stages.append(LifecycleStage("poll", "ok" if terminal else "timeout",
                                     f"종료상태={terminal or 'max_polls 초과'}"))
        if terminal in ("FAILED",) or terminal is None:
            return LifecycleReport("failed", pod_id, dataset_url, "", stages)

        # ④ 어댑터 회수
        artifact = ""
        if self._down is not None and output_url:
            ok = self._down(output_url, artifact_dest)
            artifact = artifact_dest if ok else ""
            stages.append(LifecycleStage("retrieve", "ok" if ok else "failed",
                                         f"LoRA 어댑터 → {artifact_dest}" if ok else "다운로드 실패"))
        else:
            stages.append(LifecycleStage("retrieve", "skipped", "다운로더/OUTPUT_URL 미제공"))

        # ⑤ 등재(옵션)
        if self._registry is not None and artifact:
            stages.append(LifecycleStage("register", "ok", "lora_model_registry 등재 후보"))

        return LifecycleReport("completed", pod_id, dataset_url, artifact, stages)
