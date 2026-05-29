"""Literary OS PublicSDK — Python 샘플 코드 (ADR-117)."""

from literary_system.sdk import LiteraryOSClient, SDKConfig

# ── 클라이언트 초기화 ─────────────────────────────────────────────────────
client = LiteraryOSClient(SDKConfig(offline_mode=True))

# ── 1. analyze() — 씬 분석 ───────────────────────────────────────────────
result = client.analyze(
    text="영수는 창문을 바라보았다. 눈물이 고였다. 배신감이 폭발했다.",
    context="두 사람이 처음 마주쳤다.",
)
print(f"품질 점수: {result.quality.overall:.3f}")
print(f"이슈: {result.issues}")

# ── 2. repair() — 이슈 수정 ──────────────────────────────────────────────
repair = client.repair(
    text="짧은 씬이다.",
    issues=["too_few_sentences", "text_too_short"],
    target_score=0.75,
)
print(f"수정 전: {repair.score_before:.3f} → 수정 후: {repair.score_after:.3f}")

# ── 3. predict() — 다음 씬 예측 ──────────────────────────────────────────
predict = client.predict(
    context="두 사람이 골목에서 마주쳤다. 분위기가 묘했다.",
    n=3,
    style_hint="melodrama",
)
for p in predict.predictions:
    print(f"[{p.rank}] {p.synopsis} ({p.probability:.2f})")

# ── 4. generate() — 씬 생성 ──────────────────────────────────────────────
gen = client.generate(
    title="운명의 교차로",
    characters=["이지수", "박민호"],
    setting="비 오는 골목길",
    conflict="오래된 비밀이 드러나다",
    tone="dramatic",
)
print(gen.scene_text)
print(f"품질: {gen.quality.overall:.3f} | critic PASS: {gen.passed_critic}")
