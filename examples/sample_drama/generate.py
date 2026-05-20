"""
Literary OS — 샘플 드라마 생성 스크립트 '비와 편지'

사용법:
    python examples/sample_drama/generate.py             # MOCK 모드 (API 불필요)
    python examples/sample_drama/generate.py --real      # 실 LLM (ANTHROPIC_API_KEY 필요)
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def mock_mode():
    """MOCK 모드: 인라인 게이트웨이 + MockLLMBridge 로 씬 생성."""
    from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
    from literary_system.llm_bridge.llm_context import LLMResponse
    from literary_system.pipelines.scene_generation_pipeline import (
        SceneGenerationPipeline,
        EpisodeStructureConfig,
    )

    SAMPLE_TEXTS = [
        "서진은 우산도 없이 빗속에 서 있었다. 플랫폼 저 끝에서 걸어오는 남자의 실루엣이 눈에 들어왔다. "
        "심장이 내려앉았다. 준혁이었다. 10년이라는 시간이 그의 윤곽을 조금 다듬었을 뿐, 그 걸음걸이는 여전했다.",

        "\"잘 지냈어?\" 준혁이 먼저 말을 꺼냈다. 서진은 커피잔을 두 손으로 감쌌다. "
        "따뜻한 온기가 손끝을 타고 올라왔지만, 가슴 한 켠은 여전히 서늘했다. \"응. 잘 지냈어.\" 거짓말이었다.",

        "가방 안 지갑 뒤에서 손가락이 무언가에 닿았다. 서진은 순간 호흡을 멈췄다. "
        "10년 전 부치지 못한 편지. 이미 빛바랜 봉투 위에는 수신인 이름이 흐릿하게 남아 있었다. 이름 석 자: 이준혁.",

        "준혁은 창밖을 바라보며 말했다. \"그때 나는 네가 먼저 떠난 줄 알았어.\" "
        "서진의 손이 잔 위에서 멈췄다. 긴 침묵이 카페를 채웠다. 빗소리만이 공간을 메웠다.",
    ] * 5

    _bridge = MockLLMBridge(scripted_responses=SAMPLE_TEXTS)

    class _MockGateway:
        def call(self, prompt: str, context=None) -> LLMResponse:
            text = _bridge.generate(prompt, context or {})
            return LLMResponse(text=text, provider_id="mock", latency_ms=0.0)

    config = EpisodeStructureConfig(episode_idx=1, runtime_min=5)
    pipeline = SceneGenerationPipeline(gateway=_MockGateway(), max_scenes=4)

    print("=" * 60)
    print("  Literary OS — 샘플 드라마 '비와 편지' EP01")
    print("  MOCK 모드 (실 LLM 미사용)")
    print("=" * 60)

    result = pipeline.run(config=config, episode_context={
        "series_title": "비와 편지",
        "characters": ["서진", "준혁"],
    })

    scenes = result.scenes if hasattr(result, "scenes") else []
    for i, scene in enumerate(scenes, 1):
        text = getattr(scene, "text", "") or "(빈 씬)"
        print(f"\n[씬 {i:02d}] {getattr(scene, 'scene_id', f'SC{i:02d}')}")
        print(f"  {text[:140]}{'...' if len(text) > 140 else ''}")

    elapsed = getattr(result, "total_elapsed_s", 0)
    print(f"\n총 {len(scenes)}개 씬 생성 | 소요: {elapsed:.2f}s")
    print("=" * 60)


def real_mode():
    """실 LLM 모드: Anthropic API 사용."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.stderr.write("오류: ANTHROPIC_API_KEY 환경변수가 필요합니다.\n")
        sys.exit(1)

    from literary_system.llm_bridge.adapters.anthropic_adapter import AnthropicAdapter
    from literary_system.llm_bridge.llm_context import LLMResponse
    from literary_system.pipelines.scene_generation_pipeline import (
        SceneGenerationPipeline,
        EpisodeStructureConfig,
    )

    _adapter = AnthropicAdapter(api_key=api_key)

    class _ProdGateway:
        def call(self, prompt: str, context=None) -> LLMResponse:
            text = _adapter.generate(prompt, context or {})
            return LLMResponse(text=text, provider_id="anthropic", latency_ms=0.0)

    config = EpisodeStructureConfig(episode_idx=1, runtime_min=10)
    pipeline = SceneGenerationPipeline(gateway=_ProdGateway(), max_scenes=3)

    print("=" * 60)
    print("  Literary OS — 샘플 드라마 '비와 편지' EP01")
    print("  실 LLM 모드 (Anthropic Claude)")
    print("=" * 60)

    result = pipeline.run(config=config, episode_context={
        "series_title": "비와 편지",
        "setting": "현대 서울, 로맨스 멜로",
        "characters": ["서진(30, 작가)", "준혁(32, 건축가)"],
        "theme": "10년 만의 재회, 부치지 못한 편지의 비밀",
    })

    for i, scene in enumerate(result.scenes, 1):
        print(f"\n[씬 {i:02d}] {scene.scene_id}")
        print(f"  {scene.text[:300]}")

    print(f"\n총 {len(result.scenes)}개 씬 생성 | 소요: {result.total_elapsed_s:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Literary OS 샘플 드라마 생성")
    parser.add_argument("--real", action="store_true", help="실 LLM 모드 (ANTHROPIC_API_KEY 필요)")
    args = parser.parse_args()
    real_mode() if args.real else mock_mode()
