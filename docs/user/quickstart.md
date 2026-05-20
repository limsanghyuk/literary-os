# Literary OS — 빠른 시작 (Quickstart)

> 5분 안에 첫 번째 한국 드라마 씬을 생성하세요.

---

## 사전 요건

```
Python 3.11+
pip install literary-os  # 또는 git clone 후 pip install -e ".[dev]"
```

## 1. 설치 확인

```bash
python -c "from literary_system.gates.release_gate import run_release_gate; print('OK')"
```

## 2. 첫 씬 생성 (MOCK 모드 — API 키 불필요)

```python
from literary_system.scene_generation.pipeline import SceneGenerationPipeline
from literary_system.llm_bridge.mock_bridge import MockLLMBridge

class MockGateway:
    def __init__(self):
        self._bridge = MockLLMBridge(scripted_responses=[
            "주인공 서진은 창가에 서서 빗소리를 들었다. "
            "그녀의 손에는 아직 읽지 못한 편지 한 통이 쥐어져 있었다."
        ])
    def call(self, prompt, ctx=None):
        return self._bridge.generate(prompt)

pipeline = SceneGenerationPipeline(gateway=MockGateway())
result = pipeline.generate(scene_id="EP01_SC01", prompt="빗속의 이별")
print(result.text)
```

출력:
```
주인공 서진은 창가에 서서 빗소리를 들었다. 그녀의 손에는 아직 읽지 못한 편지 한 통이 쥐어져 있었다.
```

## 3. 실 LLM 연결 (Anthropic)

```python
from literary_system.llm_bridge.anthropic_adapter import AnthropicAdapter
from literary_system.scene_generation.pipeline import SceneGenerationPipeline
import os

adapter = AnthropicAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])

class ProdGateway:
    def __init__(self, adapter): self._a = adapter
    def call(self, prompt, ctx=None): return self._a.generate(prompt)

pipeline = SceneGenerationPipeline(gateway=ProdGateway(adapter))
result = pipeline.generate(scene_id="EP01_SC01", prompt="빗속의 이별")
print(result.text)
```

## 4. Release Gate 실행

```bash
python -c "
from literary_system.gates.release_gate import run_release_gate
r = run_release_gate()
print(f\"Gates: {r['gates_passed']}/{r['total_gates']}\")
"
# Gates: 45/45
```

## 5. E2E 테스트 실행

```bash
python -m pytest tests/e2e/ -v -m "not real_llm"
# 20 passed in 0.34s
```

---

## 다음 단계

- [How-to 가이드](howto.md) — 실제 드라마 에피소드 생성
- [API 레퍼런스](reference.md) — 모든 클래스·함수 목록
- [아키텍처 설명](explanation.md) — Literary OS 설계 원리
