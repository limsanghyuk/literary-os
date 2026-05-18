#!/usr/bin/env bash
# create_release.sh — GitHub Release v7.7.1-V571 생성
# 사전 조건: gh auth login, git tag v7.7.1-V571 존재
set -e

TAG="v7.7.1-V571"
ZIP="literary_os_${TAG}.zip"

[ -f "$ZIP" ] || {
  echo "ZIP 빌드 중..."
  zip -r "$ZIP" . \
    --exclude "__pycache__/*" --exclude "**/__pycache__/*" \
    --exclude "*.pyc" --exclude ".pytest_cache/*" \
    --exclude "**/.pytest_cache/*" --exclude ".git/*" -q
}

sha256sum "$ZIP" > "${ZIP}.sha256"
echo "$(sha256sum "$ZIP")" >> SHA256SUMS.txt

gh release create "$TAG" \
  --title "Literary OS V571 — Phase 6 MultiWork Stage C" \
  --notes-file RELEASE_NOTES.md \
  "$ZIP" "${ZIP}.sha256" SHA256SUMS.txt RELEASE_INFO.txt

echo "릴리즈 완료: https://github.com/limsanghyuk/literary-os/releases/tag/$TAG"
