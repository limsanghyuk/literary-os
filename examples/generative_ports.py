# -*- coding: utf-8 -*-
"""GenerativePort 구현 — 배선 오케스트레이터의 생성 좌석 교체분.
계약(불변): generate(prompt: str, *, episode_idx: int) -> str  (wiring_poc.GenerativePort)
- FrontierPort: OpenAI/Claude API (샌드박스 가용, LLM-2 좌석 프록시). curl 사용(urllib hang 회피).
- LLM1Port: 졸업한 Llama-3.1-8B + lora_v3 어댑터 (집 RTX 4070 전용; lazy import).
"""
from __future__ import annotations
import os, json, subprocess, re
from dataclasses import dataclass

SCENE_SYS = (
    "너는 한국 드라마 대본 작가다. 주어진 회차 브리프에 맞춰 그 회차의 **오프닝 한 장면**을 "
    "한국어 대본체(지문+대사)로 써라. 분량 250~400자. 설명(tell)이 아니라 행동·대사로 보여줘라(show). "
    "브리프의 인물·갈등압력·payoff 지시를 반영하되, 메타설명·머리말 없이 장면만 출력."
)

@dataclass
class FrontierPort:
    """LLM-2 좌석 프록시 / 물-흘리기용. OpenAI gpt-4o-mini 기본."""
    model: str = "gpt-4o-mini"
    name: str = "frontier-openai"
    max_tokens: int = 600
    def _key(self) -> str:
        k = os.environ.get("OPENAI_API_KEY")
        if not k and os.path.exists("/tmp/.oai"):
            k = open("/tmp/.oai").read().strip()
        if not k:
            raise RuntimeError("OPENAI_API_KEY 없음")
        return k
    def generate(self, prompt: str, *, episode_idx: int) -> str:
        body = json.dumps({"model": self.model, "temperature": 0.8, "max_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": SCENE_SYS},
                         {"role": "user", "content": prompt}]})
        r = subprocess.run(["curl", "-s", "--max-time", "40",
            "https://api.openai.com/v1/chat/completions",
            "-H", f"Authorization: Bearer {self._key()}",
            "-H", "Content-Type: application/json", "-d", body],
            capture_output=True, text=True)
        try:
            return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[FRONTIER-ERR ep{episode_idx:02d}] {e} :: {r.stdout[:120]}"


@dataclass
class LLM1Port:
    """집 RTX 4070 전용: Llama-3.1-8B-Instruct + lora_v3 어댑터(졸업본).
    샌드박스에선 인스턴스화 금지(GPU/16GB 모델 부재). 계약만 동일."""
    base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    adapter_dir: str = r"C:\claude\4070_oneclick\lora_v3_5"
    name: str = "llm1-8b-lora-v3"
    _pipe = None
    def _load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        tok = AutoTokenizer.from_pretrained(self.base_model)
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model, torch_dtype=torch.float16, device_map="auto", load_in_4bit=True)
        model = PeftModel.from_pretrained(model, self.adapter_dir)
        model.eval()
        self._pipe = (tok, model)
    def generate(self, prompt: str, *, episode_idx: int) -> str:
        if self._pipe is None:
            self._load()
        import torch
        tok, model = self._pipe
        msgs = [{"role": "system", "content": SCENE_SYS}, {"role": "user", "content": prompt}]
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=400, do_sample=True, temperature=0.8, top_p=0.9)
        return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
