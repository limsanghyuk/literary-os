"""
finetune/runpod_real_adapter.py — RunPod 실 REST API 어댑터 (V772, ADR-232).

V590의 RunPodAdapter는 Mock(실 API 미연동)이었다. 본 어댑터는 RunPod REST v1을
**실제로 호출**한다 — API 키(Bearer)를 주면 POST /pods로 실 GPU 파드를 생성해 학습을 띄운다.
키가 없거나 dry_run이면 네트워크 없이 추정만(안전).

LLM-0: GPU 학습 인프라 호출이지 LLM 추론 호출이 아님.
보안: api_key는 인자/환경변수에서만 받음. 로깅·직렬화에 키를 포함하지 않음.
참조: https://docs.runpod.io/api-reference/pods/POST/pods (Bearer auth, REST v1)
"""
from __future__ import annotations
import json as _json
import os
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, Optional, Tuple

from literary_system.finetune.gpu_adapter import (
    GPUAdapterContract, GPUProvider, GPUJobStatus, GPUJobRequest, GPUJobResult)

RUNPOD_REST_BASE = "https://rest.runpod.io/v1"
DEFAULT_IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
DEFAULT_GPU_TYPE = "NVIDIA GeForce RTX 4090"   # 12~24GB QLoRA 적합, 저가

# transport: (method, url, headers, body_bytes|None) -> (status_code, response_dict)
Transport = Callable[[str, str, Dict[str, str], Optional[bytes]], Tuple[int, Dict[str, Any]]]


def _urllib_transport(method: str, url: str, headers: Dict[str, str],
                      body: Optional[bytes]) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8") or "{}"
            return r.status, _json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            return e.code, _json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:                       # 네트워크 실패 등
        return 0, {"error": str(e)}


class RealRunPodAdapter(GPUAdapterContract):
    """RunPod REST v1 실 어댑터 — 키 제공 시 실제 파드 생성."""

    _PROVIDER_ID   = GPUProvider.RUNPOD
    _COST_PER_HOUR = 0.39

    def __init__(self, api_key: str = "", gpu_type_id: str = DEFAULT_GPU_TYPE,
                 image_name: str = DEFAULT_IMAGE, cost_override: Optional[float] = None,
                 transport: Optional[Transport] = None) -> None:
        self._api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self._gpu = gpu_type_id
        self._image = image_name
        self._cost_ph = cost_override if cost_override is not None else self._COST_PER_HOUR
        self._transport = transport or _urllib_transport

    # ── 계약 ────────────────────────────────────────────────
    @property
    def provider_id(self) -> GPUProvider:
        return self._PROVIDER_ID

    @property
    def cost_per_hour(self) -> float:
        return self._cost_ph

    def estimate_cost(self, hours: float) -> float:
        return round(hours * self._cost_ph, 4)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str,
                 body: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        data = _json.dumps(body).encode("utf-8") if body is not None else None
        return self._transport(method, RUNPOD_REST_BASE + path, self._headers(), data)

    def verify_key(self) -> bool:
        """GET /pods로 키 유효성 확인(200=유효). 키 없으면 False."""
        if not self._api_key:
            return False
        status, _ = self._request("GET", "/pods")
        return status == 200

    def dry_run(self, request: GPUJobRequest) -> GPUJobResult:
        """네트워크 없이 비용 추정만."""
        return GPUJobResult(
            job_id=request.job_id, provider=self._PROVIDER_ID, status=GPUJobStatus.DRY_RUN,
            actual_hours=request.hours_estimate, cost_usd=self.estimate_cost(request.hours_estimate),
            dry_run=True, artifact_path="",
            metadata={"gpu_type": self._gpu, "image": self._image,
                      "model_name": request.model_name, "real_api": True, "has_key": bool(self._api_key)})

    def _pod_payload(self, request: GPUJobRequest) -> Dict[str, Any]:
        """POST /pods 페이로드 — 학습 파라미터를 env로 주입."""
        return {
            "name": f"litos-train-{request.job_id}",
            "imageName": self._image,
            "gpuTypeIds": [self._gpu],
            "gpuCount": 1,
            "containerDiskInGb": 40,
            "volumeInGb": 20,
            "env": {
                "BASE_MODEL": request.model_name,
                "DATASET": request.dataset_path,
                "DATASET_URL": str(request.extra.get("dataset_url", "")),
                "OUTPUT_URL": str(request.extra.get("output_url", "")),
                "OBJECTIVE": str(request.extra.get("objective", "dpo")),
                "RLAIF": "1",
            },
            # 기동 스크립트: DATASET_URL 다운로드 → 학습 → OUTPUT_URL 업로드(운영 동기화)
            "dockerStartCmd": ["bash", "-lc",
                               "set -e; D=/workspace/dpo.jsonl; "
                               "[ -n \"$DATASET_URL\" ] && curl -fsSL \"$DATASET_URL\" -o $D || cp \"$DATASET\" $D; "
                               "python -m literary_system.finetune.train_local --dataset $D --base $BASE_MODEL --out /workspace/lora_out; "
                               "[ -n \"$OUTPUT_URL\" ] && curl -fsS -T /workspace/lora_out/adapter_model.safetensors \"$OUTPUT_URL\" || true"],
        }

    def launch_job(self, request: GPUJobRequest) -> GPUJobResult:
        """
        실 파드 생성. dry_run=True거나 키 없으면 dry_run으로 위임(안전).
        키 있으면 POST /pods 실제 호출.
        """
        if request.dry_run or not self._api_key:
            return self.dry_run(request)
        status, data = self._request("POST", "/pods", self._pod_payload(request))
        if status not in (200, 201):
            return GPUJobResult(
                job_id=request.job_id, provider=self._PROVIDER_ID, status=GPUJobStatus.FAILED,
                actual_hours=0.0, cost_usd=0.0, dry_run=False,
                error=f"RunPod API {status}: {str(data.get('error', data))[:160]}",
                metadata={"http_status": status})
        pod_id = data.get("id") or data.get("podId") or ""
        return GPUJobResult(
            job_id=request.job_id, provider=self._PROVIDER_ID, status=GPUJobStatus.RUNNING,
            actual_hours=request.hours_estimate, cost_usd=self.estimate_cost(request.hours_estimate),
            dry_run=False, artifact_path=f"runpod://pods/{pod_id}",
            metadata={"pod_id": pod_id, "gpu_type": self._gpu, "http_status": status,
                      "poll": f"GET {RUNPOD_REST_BASE}/pods/{pod_id}"})

    def poll(self, pod_id: str) -> Dict[str, Any]:
        """파드 상태 조회(운영 폴링용)."""
        status, data = self._request("GET", f"/pods/{pod_id}")
        return {"http_status": status, "desiredStatus": data.get("desiredStatus"),
                "pod_id": pod_id, "raw_keys": list(data.keys())}


def make_real_runpod(api_key: str = "", **kw) -> RealRunPodAdapter:
    """팩토리 — 키는 인자 또는 RUNPOD_API_KEY env."""
    return RealRunPodAdapter(api_key=api_key, **kw)
