#!/bin/bash
# tools/install_hooks.sh — Literary OS Git Hooks 설치 스크립트
#
# 사용법 (집/회사 로컬 환경에서 git clone 후 1회 실행):
#   bash tools/install_hooks.sh
#
# 설치되는 Hook:
#   .git/hooks/pre-commit  — 커밋 전 LLM-0/Gate/DEV_MODE 위반 자동 차단

set -e

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
HOOKS_DIR="$ROOT/.git/hooks"
TOOLS_DIR="$ROOT/tools"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Literary OS Git Hooks 설치 (DEV_PROTOCOL_v2.0)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "  ❌ .git/hooks 디렉토리 없음 — git 저장소인지 확인하세요"
    exit 1
fi

# pre-commit hook 설치
PRE_COMMIT_SRC="$TOOLS_DIR/hooks/pre-commit"
PRE_COMMIT_DST="$HOOKS_DIR/pre-commit"

if [ ! -f "$PRE_COMMIT_SRC" ]; then
    echo "  ❌ tools/hooks/pre-commit 없음"
    exit 1
fi

cp "$PRE_COMMIT_SRC" "$PRE_COMMIT_DST"
chmod +x "$PRE_COMMIT_DST"
echo "  ✅ pre-commit hook 설치: $PRE_COMMIT_DST"

# 설치 확인
echo ""
echo "  설치된 Hook 목록:"
ls -la "$HOOKS_DIR/" | grep -v "^total" | grep -v "sample" | grep -v "^d" | awk '{print "    " $NF " (" $1 ")"}'

echo ""
echo "  ✅ 설치 완료"
echo ""
echo "  다음 단계: python3 tools/session_start.py  (세션 시작 프로토콜)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
