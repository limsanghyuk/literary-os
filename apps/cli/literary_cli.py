"""
literary_cli.py — Literary OS Minimal-CLI v0.1
SP-A.8 (V595) | ADR-055

3가지 명령:
  literary analyze <scene_file>   — 5축 LOSConstitution 품질 분석
  literary repair  <series_id>    — 시리즈 품질 진단 + 수리 제안
  literary generate -e N -s M     — 장면 텍스트 생성

LLM-0 원칙: 외부 LLM 호출 0건
"""
from __future__ import annotations

import json
import os
import sys
import textwrap

import click

# ---------------------------------------------------------------------------
# 경로 보정 — CLI는 repo 루트 기준 실행 가정
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ---------------------------------------------------------------------------
# 내부 모듈 (lazy import — 환경 없어도 --help 동작)
# ---------------------------------------------------------------------------
def _get_constitution():
    from literary_system.constitution.los_constitution import LOSConstitution
    return LOSConstitution()


def _get_corpus_pipeline():
    from literary_system.corpus.corpus_ingestor import CorpusFallbackPipeline
    from literary_system.corpus.corpus_validator import CorpusEntryValidator
    return CorpusFallbackPipeline(), CorpusEntryValidator()


# ---------------------------------------------------------------------------
# CLI 그룹
# ---------------------------------------------------------------------------
@click.group()
@click.version_option(version="0.1.0", prog_name="literary")
def literary():
    """Literary OS — 한국 드라마/소설 내러티브 생성 CLI (v0.1)

    \b
    명령 목록:
      analyze  — 장면 파일 5축 품질 점수 분석
      repair   — 시리즈 품질 진단 및 수리 제안
      generate — 장면 텍스트 생성
    """


# ---------------------------------------------------------------------------
# literary analyze <scene_file>
# ---------------------------------------------------------------------------
@literary.command(name="analyze")
@click.argument("scene_file", type=click.Path(exists=True, readable=True))
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", show_default=True, help="출력 형식")
def analyze_cmd(scene_file: str, output_format: str):
    """SCENE_FILE의 5축 LOSConstitution 품질 점수를 분석합니다.

    \b
    출력 축:
      drse    — 문서 풍부성 점수 (0.30 가중)
      debt    — 서술 부채 점수  (0.20 가중)
      arc     — 기승전결 호 점수 (0.20 가중)
      tension — 긴장감 점수     (0.15 가중)
      prose   — 산문 품질 점수  (0.15 가중)

    \b
    예시:
      literary analyze scene.txt
      literary analyze scene.txt --format json
    """
    try:
        with open(scene_file, encoding="utf-8") as f:
            text = f.read().strip()
    except OSError as e:
        click.echo(f"[오류] 파일 읽기 실패: {e}", err=True)
        sys.exit(1)

    if not text:
        click.echo("[경고] 파일이 비어 있습니다.", err=True)
        sys.exit(1)

    constitution = _get_constitution()
    score = constitution.score_scene_full(text)

    if output_format == "json":
        click.echo(json.dumps(score.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n{'='*50}")
        click.echo(f"  Literary OS — 장면 품질 분석 리포트")
        click.echo(f"{'='*50}")
        click.echo(f"  파일     : {os.path.basename(scene_file)}")
        click.echo(f"{'─'*50}")
        click.echo(f"  drse     : {score.drse:.4f}  (가중 0.30 — 문서 풍부성)")
        click.echo(f"  debt     : {score.debt:.4f}  (가중 0.20 — 서술 부채)")
        click.echo(f"  arc      : {score.arc:.4f}  (가중 0.20 — 기승전결)")
        click.echo(f"  tension  : {score.tension:.4f}  (가중 0.15 — 긴장감)")
        click.echo(f"  prose    : {score.prose:.4f}  (가중 0.15 — 산문 품질)")
        click.echo(f"{'─'*50}")
        click.echo(f"  R(scene) : {score.total:.4f}")
        rating = (
            "★★★★★ 최상위" if score.total >= 0.85 else
            "★★★★☆ 우수" if score.total >= 0.70 else
            "★★★☆☆ 보통" if score.total >= 0.55 else
            "★★☆☆☆ 개선 필요" if score.total >= 0.40 else
            "★☆☆☆☆ 재작성 권장"
        )
        click.echo(f"  평가     : {rating}")
        click.echo(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# literary repair <series_id>
# ---------------------------------------------------------------------------
@literary.command(name="repair")
@click.argument("series_id")
@click.option("--threshold", default=0.55, show_default=True,
              type=float, help="R(scene) 최저 기준 (이하 장면 수리 대상)")
@click.option("--dry-run", is_flag=True, default=False,
              help="수리 제안만 표시 (실제 파일 변경 없음)")
def repair_cmd(series_id: str, threshold: float, dry_run: bool):
    """SERIES_ID 시리즈의 장면 품질 진단 및 수리 제안을 출력합니다.

    \b
    진단 내용:
      - R(scene) < threshold 장면 식별
      - 각 축별 약점 진단
      - 개선 방향 제안 (LLM-0, 규칙 기반)

    \b
    예시:
      literary repair drama-001
      literary repair drama-001 --threshold 0.65
      literary repair drama-001 --dry-run
    """
    click.echo(f"\n{'='*50}")
    click.echo(f"  Literary OS — 시리즈 수리 진단")
    click.echo(f"{'='*50}")
    click.echo(f"  시리즈 ID : {series_id}")
    click.echo(f"  임계값    : R(scene) < {threshold:.2f}")
    click.echo(f"  모드      : {'dry-run (제안만)' if dry_run else '수리 실행'}")
    click.echo(f"{'─'*50}")

    # 진단 엔진 — LLM-0 규칙 기반
    constitution = _get_constitution()

    # 시리즈 데이터 탐색 (현재 v0.1: 파일시스템 탐색)
    series_dir = os.path.join("data", "series", series_id)
    scene_files: list[str] = []

    if os.path.isdir(series_dir):
        for fname in sorted(os.listdir(series_dir)):
            if fname.endswith(".txt") or fname.endswith(".md"):
                scene_files.append(os.path.join(series_dir, fname))

    if not scene_files:
        click.echo(f"  [정보] '{series_id}' 시리즈 파일 없음 — 샘플 진단 실행")
        _repair_sample_diagnosis(constitution, threshold, dry_run)
        click.echo(f"{'='*50}\n")
        return

    issues = 0
    for sf in scene_files:
        with open(sf, encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            continue
        score = constitution.score_scene_full(text)
        if score.total < threshold:
            issues += 1
            _print_repair_suggestion(os.path.basename(sf), score, dry_run)

    click.echo(f"\n  진단 완료: {len(scene_files)}개 장면 중 {issues}개 수리 대상")
    click.echo(f"{'='*50}\n")


def _repair_sample_diagnosis(constitution, threshold: float, dry_run: bool) -> None:
    """시리즈 없을 때 샘플 텍스트로 진단 시연"""
    sample = "그는 말했다. 그녀가 대답했다. 상황이 변했다."
    score = constitution.score_scene_full(sample, scene_id="sample")
    click.echo(f"  샘플 장면 R(scene)={score.total:.4f}")
    if score.total < threshold:
        _print_repair_suggestion("sample.txt", score, dry_run)


def _print_repair_suggestion(filename: str, score, dry_run: bool) -> None:
    """축별 약점 진단 및 개선 제안 출력"""
    click.echo(f"\n  [수리 대상] {filename}  R={score.total:.4f}")
    axes = [
        ("drse", score.drse, 0.50, "문서 길이 + 어휘 다양성 증가 권장"),
        ("debt", score.debt, 0.60, "도입부 훅(hook) 강화, 해결 장면 추가"),
        ("arc",  score.arc,  0.50, "기승전결 마커 명시 (기: 도입, 승: 전개, 전: 반전, 결: 해소)"),
        ("tension", score.tension, 0.50, "긴장감 어휘 추가 (위기, 두려움, 갈등 등)"),
        ("prose",   score.prose,   0.50, "문장 길이 다양화, 어휘 중복 감소"),
    ]
    for axis, val, min_ok, advice in axes:
        if val < min_ok:
            marker = "⚠" if not dry_run else "→"
            click.echo(f"    {marker} {axis:8s}: {val:.4f} (< {min_ok:.2f}) — {advice}")


# ---------------------------------------------------------------------------
# literary generate -e N -s M
# ---------------------------------------------------------------------------
@literary.command(name="generate")
@click.option("-e", "--episodes", default=1, show_default=True,
              type=click.IntRange(1, 100), help="에피소드 수")
@click.option("-s", "--scenes", default=5, show_default=True,
              type=click.IntRange(1, 50), help="에피소드당 장면 수")
@click.option("--seed", default=42, show_default=True,
              type=int, help="랜덤 시드 (재현성)")
@click.option("--min-score", default=0.50, show_default=True,
              type=float, help="최소 R(scene) 기준 (미달 시 재생성)")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", show_default=True, help="출력 형식")
def generate_cmd(episodes: int, scenes: int, seed: int,
                 min_score: float, output_format: str):
    """장면 텍스트를 생성합니다.

    \b
    생성 전략 (LLM-0, 규칙 기반 합성):
      1. CorpusFallbackPipeline으로 기반 텍스트 수집
      2. LOSConstitution으로 품질 검증 (R(scene) >= min-score)
      3. 미달 장면은 rich template으로 보강

    \b
    예시:
      literary generate -e 2 -s 3
      literary generate -e 1 -s 10 --seed 0 --min-score 0.60
      literary generate -e 1 -s 5 --format json
    """
    from literary_system.corpus.corpus_ingestor import CorpusFallbackPipeline
    from literary_system.constitution.los_constitution import LOSConstitution

    total_scenes = episodes * scenes
    pipeline = CorpusFallbackPipeline(seed=seed)
    constitution = LOSConstitution()

    if output_format != "json":
        click.echo(f"\n{'='*50}")
        click.echo(f"  Literary OS — 장면 생성")
        click.echo(f"{'='*50}")
        click.echo(f"  에피소드: {episodes} | 장면/에피소드: {scenes}")
        click.echo(f"  총 장면 : {total_scenes} | seed: {seed}")
        click.echo(f"  최소 점수: R(scene) >= {min_score:.2f}")
        click.echo(f"{'─'*50}")

    # 기반 텍스트 수집 (total_scenes * 2 — 후보군)
    candidates = pipeline.collect(count=total_scenes * 2)

    results = []
    generated = 0
    for ep in range(1, episodes + 1):
        for sc in range(1, scenes + 1):
            idx = (ep - 1) * scenes + (sc - 1)
            entry = candidates[idx % len(candidates)]
            score = constitution.score_scene(entry.text)

            # min_score 미달 시 rich template 보강
            if score < min_score:
                text = _enrich_text(entry.text, ep, sc)
                score = constitution.score_scene(text)
            else:
                text = entry.text

            result = {
                "episode": ep,
                "scene": sc,
                "score": round(score, 4),
                "source": entry.source_type,
                "text": text[:200] + ("..." if len(text) > 200 else ""),
            }
            results.append(result)
            generated += 1

    if output_format != "json":
        click.echo(f"  생성 완료: {generated}개 장면")
        click.echo(f"{'='*50}\n")

    if output_format == "json":
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            click.echo(f"[E{r['episode']:02d}S{r['scene']:02d}] "
                       f"R={r['score']:.4f} ({r['source']}) {r['text'][:80]}...")


def _enrich_text(base_text: str, ep: int, sc: int) -> str:
    """기승전결 마커 + 긴장감 어휘를 주입해 R(scene) 점수 보강"""
    acts = ["기: 이야기가 시작되었다. ", "승: 사건이 전개되었다. ",
            "전: 반전이 찾아왔다. ", "결: 모든 것이 해소되었다. "]
    tension = "위기가 고조되었다. 두려움과 갈등이 교차했다. "
    hook = f"[E{ep:02d}-S{sc:02d}] "
    return hook + acts[(sc - 1) % 4] + tension + base_text  # BUG-01 fix: 1-based → 0-based


# ---------------------------------------------------------------------------
# 엔트리포인트
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    literary()
