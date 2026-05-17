"""V328 Task14: LLMNodeRouter — ComfyUI 스타일 멀티 어댑터 라우터 (단절 G)."""
from __future__ import annotations
from enum import Enum
from typing import Any
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface

class RoutingPolicy(str, Enum):
    PRIMARY     = "primary"
    FALLBACK    = "fallback"
    ROUND_ROBIN = "round_robin"
    QUALITY     = "quality"

class _AdapterNode:
    def __init__(self, name: str, adapter: LLMBridgeInterface, priority: int):
        self.name     = name
        self.adapter  = adapter
        self.priority = priority
        self.calls    = 0
        self.errors   = 0

class LLMNodeRouter(LLMBridgeInterface):
    def __init__(self, policy: RoutingPolicy = RoutingPolicy.FALLBACK):
        self.policy  = policy
        self._nodes: list[_AdapterNode] = []
        self._rr_idx = 0

    def register(self, name: str, adapter: LLMBridgeInterface,
                 priority: int = 0) -> "LLMNodeRouter":
        self._nodes.append(_AdapterNode(name, adapter, priority))
        self._nodes.sort(key=lambda n: -n.priority)
        return self

    @property
    def provider_name(self) -> str:
        return "llm_node_router"

    def parse_action_packet(self, raw: str):
        try:
            from literary_system.llm_bridge.tool_use_parser import ActionPacketParser
            return ActionPacketParser().parse(raw)
        except Exception:
            return None

    def generate(self, prompt: str, context=None, **kwargs) -> str:
        # Bug-Fix: added context param to match LLMBridgeInterface.generate(prompt, context)
        # UnifiedLLMGateway calls adapter.generate(prompt, ctx) positionally — **kwargs alone
        # would raise TypeError with 3 positional args (self, prompt, ctx).
        if not self._nodes:
            return "[LLMNodeRouter] no adapters registered"
        if self.policy == RoutingPolicy.ROUND_ROBIN:
            node = self._nodes[self._rr_idx % len(self._nodes)]
            self._rr_idx += 1
            return self._call(node, prompt, **kwargs)
        # PRIMARY / FALLBACK / QUALITY: try in priority order
        last_err = None
        for node in self._nodes:
            try:
                result = self._call(node, prompt, **kwargs)
                if result:
                    return result
            except Exception as e:
                last_err = e
                node.errors += 1
        return f"[LLMNodeRouter fallback] {last_err}"

    def _call(self, node: _AdapterNode, prompt: str, **kwargs) -> str:
        node.calls += 1
        # Bug-Fix: Ensure 'context' kwarg present for positional-arg adapters
        if 'context' not in kwargs:
            kwargs['context'] = {}
        return node.adapter.generate(prompt, **kwargs)

    def stats(self) -> dict:
        """노드별 호출 통계 반환 (Bug-Fix D: 누락된 public API 추가)."""
        return {
            n.name: {
                "calls":  n.calls,
                "errors": n.errors,
            }
            for n in self._nodes
        }
