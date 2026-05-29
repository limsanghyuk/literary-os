#!/usr/bin/env bash
# V587: GitHub Release 생성 도구 (V571 하드코딩 제거 — ADR-048)
# 사용법: ./tools/create_release.sh [TAG]
#   TAG 미지정 시 최신 git tag 자동 사용
# 사전 조건: gh auth login 완료
set -euo pipefail

# ── TAG 결정 ──────────────────────────────────────────────────────────────────
if [ $# -ge 1 ]; then
  TAG="$1"
else
  TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "$TAG" ]; then
  echo "❌ TAG를 찾을 수 없습니다. 사용법: $0 <TAG>"
  exit 1
fi

SEMVER=$(echo "$TAG" | grep -oP '\d+\.\d+\.\d+' | head -1)
VNUM=$(echo "$TAG"   | grep -oP 'V\d+' | head -1 || echo "")
echo "▶ Release 생성: $TAG  (semver=$SEMVER, vnum=$VNUM)"

# ── Changelog 섹션 추출 ───────────────────────────────────────────────────────
BODY_FILE="/tmp/release_body_${TAG}.md"
python tools/extract_changelog_section.py --version "$SEMVER" --output "$BODY_FILE" \
  || echo "(changelog 섹션 없음 — 본문 생략)"

# ── GitHub Release 생성 ───────────────────────────────────────────────────────
RELEASE_TITLE="${VNUM:-$TAG} (v${SEMVER})"

if [ -f "$BODY_FILE" ]; then
  gh release create "$TAG" \
    --title "$RELEASE_TITLE" \
    --notes-file "$BODY_FILE"
else
  gh release create "$TAG" \
    --title "$RELEASE_TITLE" \
    --notes "Literary OS ${VNUM} — v${SEMVER}"
fi

echo "✅ GitHub Release 생성 완료: $TAG"
