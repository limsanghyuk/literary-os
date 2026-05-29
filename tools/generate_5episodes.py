#!/usr/bin/env python3
"""
tools/generate_5episodes.py
V485 — 60분 한국 드라마 5화 생성 데모 스크립트

사용:
  # Mock 모드 (API 키 불필요)
  python tools/generate_5episodes.py

  # 실 LLM 모드
  ANTHROPIC_API_KEY=sk-... python tools/generate_5episodes.py

  # 옵션
  python tools/generate_5episodes.py --episodes 3 --max-scenes 5 --output out/script.txt
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("generate_5episodes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Literary OS V485 — 드라마 생성 데모")
    parser.add_argument("--episodes", type=int, default=5, help="생성할 화 수 (기본 5)")
    parser.add_argument("--start-ep", type=int, default=0, help="시작 화 인덱스 (0-based)")
    parser.add_argument("--max-scenes", type=int, default=None, help="화당 최대 씬 수 (기본 전체)")
    parser.add_argument("--output", type=str, default=None, help="스크립트 저장 경로")
    parser.add_argument("--title", type=str, default="Literary OS 시범 드라마", help="시리즈 제목")
    args = parser.parse_args()

    from literary_system.pipelines.drama_episode_generator import (
        DramaEpisodeGenerator, DramaSeriesConfig,
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    mode = "실 LLM (Claude)" if api_key else "Mock (테스트)"

    print(f"\n{'='*60}")
    print(f"  Literary OS V485 — 드라마 생성 데모")
    print(f"  모드: {mode}")
    print(f"  생성: {args.start_ep + 1}화 ~ {args.start_ep + args.episodes}화")
    if args.max_scenes:
        print(f"  화당 최대 씬: {args.max_scenes}개")
    print(f"{'='*60}\n")

    series_config = DramaSeriesConfig(
        title=args.title,
        total_episodes=16,
        runtime_min=60.0,
    )

    generator = DramaEpisodeGenerator.from_env(
        series_config=series_config,
        max_scenes_per_episode=args.max_scenes,
    )

    result = generator.generate_series(
        n_episodes=args.episodes,
        start_episode=args.start_ep,
    )

    # 결과 요약 출력
    print(f"\n{'='*60}")
    print(f"  생성 완료")
    print(f"{'='*60}")
    summary = result.to_dict()
    print(f"  총 화수: {summary['total_episodes_generated']}")
    print(f"  총 씬수: {summary['total_scenes_generated']}")
    print(f"  총 단어: {summary['total_word_count']:,}")
    print(f"  성공률: {summary['success_rate']:.1%}")
    print(f"  소요시간: {summary['total_elapsed_s']:.1f}초")
    print()
    for ep in summary["episodes"]:
        print(f"  {ep['episode']}화: {ep['scenes']}씬 / {ep['words']:,}단어 / {ep['elapsed_s']:.1f}s")

    # 파일 저장
    if args.output:
        script = result.full_script()
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"\n  스크립트 저장됨: {args.output}")
    else:
        # stdout에 첫 화만 출력
        if result.episode_results:
            first = result.episode_results[0]
            print(f"\n{'─'*60}")
            print(f"  1화 첫 씬 미리보기")
            print(f"{'─'*60}")
            first_scene = next((s for s in first.scenes if s.success), None)
            if first_scene:
                preview = first_scene.text[:500]
                print(preview)
                if len(first_scene.text) > 500:
                    print("  ...(생략)...")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
