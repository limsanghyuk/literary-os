"""
V453 — RealOllamaAdapter
로컬 Ollama HTTP API 실 연결 어댑터.
- /api/chat  : 채팅 완성 (스트림 지원)
- /api/tags  : 모델 목록 / pull 상태 확인
- /api/pull  : 모델 자동 pull
- GPU 메모리 모니터링 (VRAM 사용량 추적)
LLM-0 원칙: call_fn 주입으로 CI에서 실 API 호출 없음 보장.
"""
from __future__ import annotations

import json
import os
import time
import uuid
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from literary_system.adapters_live.real_claude_adapter import (
    RealLLMResponse,
    LiveAdapterCall,
    _count_tokens,
    _backoff_delay,
)


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

@dataclass
class RealOllamaAdapterConfig:
    """RealOllamaAdapter 설정."""
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    max_tokens: int = 4096
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 32.0
    timeout_s: float = 60.0          # Ollama는 로컬 GPU 추론 — 더 긴 타임아웃
    auto_pull: bool = True           # 모델 미존재 시 자동 pull
    pull_timeout_s: float = 300.0    # pull 최대 대기
    # Ollama는 무료 로컬 실행 — 비용 0
    input_price_per_1k: float = 0.0
    output_price_per_1k: float = 0.0
    # GPU 메모리 임계치 경고 (바이트). 0 = 비활성화
    gpu_memory_warning_bytes: int = 0

    # BGE-M3 임베딩 전용 모델 별명
    EMBEDDING_MODELS = frozenset({"bge-m3", "nomic-embed-text", "mxbai-embed-large"})


# ---------------------------------------------------------------------------
# GPU 메모리 스냅샷
# ---------------------------------------------------------------------------

@dataclass
class GPUMemorySnapshot:
    """GPU 메모리 상태 스냅샷."""
    timestamp_ms: float
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    utilization_pct: float = 0.0
    source: str = "unknown"  # "nvidia-smi" | "ollama-api" | "unavailable"

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024 ** 3)


# ---------------------------------------------------------------------------
# 어댑터
# ---------------------------------------------------------------------------

class RealOllamaAdapter:
    """
    Ollama 로컬 서버 실 연결 어댑터 (V453).

    Parameters
    ----------
    config : RealOllamaAdapterConfig, optional
    call_fn : Callable, optional
        LLM-0 주입 함수. 시그니처: (**kwargs) → dict
        kwargs keys: url, payload, timeout
        반환: {"content": str, "input_tokens": int, "output_tokens": int,
               "model": str, "eval_duration_ns": int}
    http_fn : Callable, optional
        HTTP GET 주입 (health_check, model list 등). 시그니처: (url, timeout) → dict
    tenant_id : str
    """

    def __init__(
        self,
        config: Optional[RealOllamaAdapterConfig] = None,
        call_fn: Optional[Callable] = None,
        http_fn: Optional[Callable] = None,
        tenant_id: str = "default",
    ) -> None:
        self.config = config or RealOllamaAdapterConfig()
        self._call_fn = call_fn
        self._http_fn = http_fn      # GET 요청 주입
        self.tenant_id = tenant_id

        # 통계
        self._total_calls: int = 0
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_cost_usd: float = 0.0
        self._total_latency_ms: float = 0.0
        self._error_count: int = 0
        self._call_log: List[LiveAdapterCall] = []

        # GPU 메모리 기록
        self._gpu_snapshots: List[GPUMemorySnapshot] = []

    # ------------------------------------------------------------------
    # 핵심 인터페이스
    # ------------------------------------------------------------------

    def call(self, ctx) -> RealLLMResponse:
        """
        Ollama /api/chat 호출.

        ctx.extra 키:
          - user_prompt  : str  (필수)
          - history      : list of {"role": ..., "content": ...}
          - stream       : bool (스트리밍, 기본 False)
          - system_prompt: str (선택)
        """
        extra = ctx.extra or {}
        user_prompt: str = extra.get("user_prompt", "")
        history: List[Dict] = extra.get("history", [])
        system_prompt: str = extra.get("system_prompt", "") or getattr(ctx, "system_prompt", "") or ""
        stream: bool = extra.get("stream", False)

        model = self.config.model
        max_tokens = getattr(ctx, "max_tokens", None) or self.config.max_tokens
        timeout = getattr(ctx, "timeout", None) or self.config.timeout_s

        # 메시지 조립
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
            },
        }

        call_id = str(uuid.uuid4())
        start_ms = time.monotonic() * 1000
        retries = 0
        last_error = ""

        # 모델 자동 pull (최초 1회)
        if self.config.auto_pull and self._call_fn is None:
            try:
                self._ensure_model_available(model)
            except Exception:
                pass  # pull 실패해도 call 시도

        for attempt in range(self.config.max_retries + 1):
            try:
                url = f"{self.config.base_url}/api/chat"
                raw = self._do_call(url=url, payload=payload, timeout=timeout)
                latency_ms = time.monotonic() * 1000 - start_ms

                in_tok = raw.get("input_tokens", _count_tokens(user_prompt, model))
                out_tok = raw.get("output_tokens", _count_tokens(raw.get("content", ""), model))
                # Ollama eval_duration_ns → 실 latency 보정
                if raw.get("eval_duration_ns"):
                    latency_ms = raw["eval_duration_ns"] / 1_000_000

                cost = 0.0  # 로컬 실행 비용 없음

                self._record(call_id, model, in_tok, out_tok, cost, latency_ms, retries, True)

                # GPU 메모리 스냅샷 (가능 시)
                self._try_snapshot_gpu()

                return RealLLMResponse(
                    text=raw.get("content", ""),
                    provider="ollama",
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    tokens_used=in_tok + out_tok,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                    call_id=call_id,
                    retries=retries,
                    success=True,
                )

            except Exception as exc:
                last_error = str(exc)
                retries += 1
                if attempt < self.config.max_retries:
                    time.sleep(_backoff_delay(attempt, self.config.base_delay, self.config.max_delay))

        latency_ms = time.monotonic() * 1000 - start_ms
        self._record(call_id, model, 0, 0, 0.0, latency_ms, retries, False, last_error)
        return RealLLMResponse(
            text="",
            provider="ollama",
            latency_ms=latency_ms,
            call_id=call_id,
            retries=retries,
            success=False,
            error=last_error,
        )

    def cost_estimate(self, ctx) -> float:
        """Ollama는 로컬 실행 — 항상 0.0."""
        return 0.0

    def health_check(self) -> bool:
        """
        Ollama 서버 응답 확인.
        call_fn / http_fn 주입 시 항상 True.
        """
        if self._call_fn is not None or self._http_fn is not None:
            return True
        try:
            import urllib.request
            url = f"{self.config.base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=3.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "ollama"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model": self.config.model,
            "provider": "ollama",
            "version": "v1",
            "phase": "3-SP1",
            "base_url": self.config.base_url,
            "max_tokens": self.config.max_tokens,
            "input_price_per_1k": 0.0,
            "output_price_per_1k": 0.0,
            "auto_pull": self.config.auto_pull,
        }

    def get_rate_limits(self) -> Dict[str, Any]:
        return {
            "max_retries": self.config.max_retries,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "timeout_s": self.config.timeout_s,
        }

    def stats(self) -> Dict[str, Any]:
        calls = self._total_calls
        avg_latency = self._total_latency_ms / calls if calls else 0.0
        return {
            "total_calls": calls,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": 0.0,  # 로컬 실행
            "avg_latency_ms": round(avg_latency, 2),
            "error_count": self._error_count,
            "tenant_id": self.tenant_id,
            "gpu_snapshots": len(self._gpu_snapshots),
        }

    def reset_stats(self) -> None:
        self._total_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._total_latency_ms = 0.0
        self._error_count = 0
        self._call_log.clear()
        self._gpu_snapshots.clear()

    # ------------------------------------------------------------------
    # 모델 관리
    # ------------------------------------------------------------------

    def list_models(self) -> List[str]:
        """
        로컬에 설치된 모델 목록 반환.
        http_fn 주입 시 주입 함수 사용.
        """
        if self._http_fn is not None:
            data = self._http_fn(f"{self.config.base_url}/api/tags", self.config.timeout_s)
            return [m["name"] for m in data.get("models", [])]

        try:
            import urllib.request
            url = f"{self.config.base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=self.config.timeout_s) as resp:
                data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def is_model_available(self, model: str) -> bool:
        """로컬에 모델이 존재하는지 확인."""
        models = self.list_models()
        # "llama3.2" == "llama3.2:latest" 허용
        for m in models:
            base = m.split(":")[0]
            if m == model or base == model or base == model.split(":")[0]:
                return True
        return False

    def pull_model(self, model: str, timeout: Optional[float] = None) -> bool:
        """
        모델 pull 요청. 성공 시 True.
        call_fn 주입 환경에서는 항상 True 반환 (CI 환경).
        """
        if self._call_fn is not None:
            return True

        pull_timeout = timeout or self.config.pull_timeout_s
        try:
            import urllib.request
            url = f"{self.config.base_url}/api/pull"
            payload = json.dumps({"name": model, "stream": False}).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=pull_timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _ensure_model_available(self, model: str) -> None:
        """모델 미존재 시 pull 시도."""
        if not self.is_model_available(model):
            self.pull_model(model)

    # ------------------------------------------------------------------
    # GPU 메모리 모니터링
    # ------------------------------------------------------------------

    def get_gpu_memory(self) -> GPUMemorySnapshot:
        """
        현재 GPU 메모리 상태 조회.
        nvidia-smi → Ollama API → 불가 순으로 시도.
        """
        ts = time.monotonic() * 1000

        # 1. nvidia-smi 시도
        snap = self._gpu_from_nvidia_smi(ts)
        if snap:
            self._gpu_snapshots.append(snap)
            return snap

        # 2. Ollama /api/ps (모델 로딩 상태) 시도
        snap = self._gpu_from_ollama_api(ts)
        if snap:
            self._gpu_snapshots.append(snap)
            return snap

        # 3. 불가
        snap = GPUMemorySnapshot(
            timestamp_ms=ts,
            source="unavailable",
        )
        self._gpu_snapshots.append(snap)
        return snap

    def _try_snapshot_gpu(self) -> None:
        """호출 후 GPU 스냅샷 시도 (오류 무시)."""
        try:
            self.get_gpu_memory()
        except Exception:
            pass

    def _gpu_from_nvidia_smi(self, ts: float) -> Optional[GPUMemorySnapshot]:
        """nvidia-smi에서 GPU 메모리 파싱."""
        try:
            import subprocess
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3.0,
            )
            if result.returncode != 0:
                return None
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                return None
            total_mb = int(parts[0])
            used_mb = int(parts[1])
            free_mb = int(parts[2])
            util_pct = float(parts[3]) if len(parts) > 3 else 0.0
            return GPUMemorySnapshot(
                timestamp_ms=ts,
                total_bytes=total_mb * 1024 * 1024,
                used_bytes=used_mb * 1024 * 1024,
                free_bytes=free_mb * 1024 * 1024,
                utilization_pct=util_pct,
                source="nvidia-smi",
            )
        except Exception:
            return None

    def _gpu_from_ollama_api(self, ts: float) -> Optional[GPUMemorySnapshot]:
        """Ollama /api/ps에서 VRAM 사용량 파싱."""
        if self._http_fn is not None:
            try:
                data = self._http_fn(f"{self.config.base_url}/api/ps", 3.0)
                return self._parse_ollama_ps(data, ts)
            except Exception:
                return None

        try:
            import urllib.request
            url = f"{self.config.base_url}/api/ps"
            with urllib.request.urlopen(url, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
            return self._parse_ollama_ps(data, ts)
        except Exception:
            return None

    def _parse_ollama_ps(self, data: Dict, ts: float) -> Optional[GPUMemorySnapshot]:
        """Ollama /api/ps 응답에서 VRAM 파싱."""
        models = data.get("models", [])
        if not models:
            return None
        total_vram = sum(m.get("size_vram", 0) for m in models)
        return GPUMemorySnapshot(
            timestamp_ms=ts,
            used_bytes=total_vram,
            source="ollama-api",
        )

    # ------------------------------------------------------------------
    # 내부 호출
    # ------------------------------------------------------------------

    def _do_call(self, url: str, payload: Dict, timeout: float) -> Dict[str, Any]:
        """실제 HTTP POST 호출 (call_fn 주입 또는 urllib)."""
        if self._call_fn is not None:
            return self._call_fn(url=url, payload=payload, timeout=timeout)

        try:
            import urllib.request
        except ImportError as exc:
            raise RuntimeError("urllib 미사용 환경") from exc

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        stream = payload.get("stream", False)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if stream:
                    return self._parse_streaming_response(resp)
                else:
                    body = json.loads(resp.read().decode())
                    return self._normalize_chat_response(body)
        except Exception as exc:
            raise RuntimeError(f"Ollama HTTP 오류: {exc}") from exc

    def _normalize_chat_response(self, body: Dict) -> Dict[str, Any]:
        """Ollama /api/chat 응답 정규화."""
        message = body.get("message", {})
        content = message.get("content", "")

        # 토큰 수: Ollama API가 제공하는 경우 사용
        prompt_eval_count = body.get("prompt_eval_count", 0)
        eval_count = body.get("eval_count", 0)
        eval_duration_ns = body.get("eval_duration", 0)

        return {
            "content": content,
            "input_tokens": prompt_eval_count or _count_tokens(content),
            "output_tokens": eval_count or _count_tokens(content),
            "model": body.get("model", ""),
            "eval_duration_ns": eval_duration_ns,
            "done": body.get("done", True),
        }

    def _parse_streaming_response(self, resp) -> Dict[str, Any]:
        """스트리밍 응답 청크 결합."""
        chunks = []
        total_input = 0
        total_output = 0
        eval_duration_ns = 0
        model_name = ""

        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = chunk.get("message", {})
            content_piece = msg.get("content", "")
            if content_piece:
                chunks.append(content_piece)

            if chunk.get("done"):
                total_input = chunk.get("prompt_eval_count", 0)
                total_output = chunk.get("eval_count", 0)
                eval_duration_ns = chunk.get("eval_duration", 0)
                model_name = chunk.get("model", "")

        full_text = "".join(chunks)
        return {
            "content": full_text,
            "input_tokens": total_input or _count_tokens(full_text),
            "output_tokens": total_output or _count_tokens(full_text),
            "model": model_name,
            "eval_duration_ns": eval_duration_ns,
        }

    def _record(
        self,
        call_id: str,
        model: str,
        in_tok: int,
        out_tok: int,
        cost: float,
        latency_ms: float,
        retries: int,
        success: bool,
        error: str = "",
    ) -> None:
        self._total_calls += 1
        self._total_input_tokens += in_tok
        self._total_output_tokens += out_tok
        self._total_cost_usd += cost
        self._total_latency_ms += latency_ms
        if not success:
            self._error_count += 1
        self._call_log.append(LiveAdapterCall(
            call_id=call_id,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
            latency_ms=latency_ms,
            retries=retries,
            success=success,
            error=error,
            provider="ollama",
        ))
