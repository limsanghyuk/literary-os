# CHANGELOG — V485 COMPLETE

## 릴리즈 정보
- **버전**: V485
- **날짜**: 2026-05-16
- **기준선**: V483 (4511 PASS) → V485 (4599 PASS)
- **신규 PASS**: +88 (4511 → 4599)
- **pyproject.toml**: 4.8.3 → 4.8.5

---

## V484 — 실 LLM 어댑터 레이어

### 신규 모듈
| 파일 | 설명 |
|------|------|
| `literary_system/llm_bridge/adapters/anthropic_adapter.py` | AnthropicAdapter + HaikuAdapter + SonnetAdapter |
| `literary_system/llm_bridge/adapters/ollama_adapter.py` | OllamaAdapter (urllib 기반, stream=False) |
| `literary_system/pipelines/scene_generation_pipeline.py` | SceneGenerationPipeline + ScenePromptAssembler + GeneratedScene + SceneGenerationResult |

### 버그 수정
- `LLMContext(metadata=...)` → `LLMContext(extra=...)` (V484 구현 오타 수정)

### 테스트
- `tests/test_v484_adapters.py`: 31 PASS (AnthropicAdapter 11, OllamaAdapter 20)
- `tests/test_v484_scene_pipeline.py`: 28 PASS (Assembler 4, GeneratedScene 8, Result 7, Pipeline 9)

---

## V485 — DramaEpisodeGenerator + 데모 CLI

### 신규 모듈
| 파일 | 설명 |
|------|------|
| `literary_system/pipelines/drama_episode_generator.py` | DramaSeriesConfig + DramaEpisodeGenerator + DramaSeriesResult |
| `tools/generate_5episodes.py` | CLI 데모: --episodes, --start-ep, --max-scenes, --output, --title |

### 설계 결정
- ANTHROPIC_API_KEY 설정 시 실 3-tier (Ollama/Haiku/Sonnet)
- 미설정 시 MockLLMBridge 자동 폴백 (LLM-0 원칙 준수)
- `generate_series(n_episodes, start_episode)` API

### 테스트
- `tests/test_v485_drama_generator.py`: 29 PASS, 2 SKIP

---

## 전체 테스트 현황
```
4599 passed, 20 skipped
```
