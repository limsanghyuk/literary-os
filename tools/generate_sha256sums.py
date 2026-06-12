"""
tools/generate_sha256sums.py — SHA256SUMS.txt 생성·검증 모듈 (V746, ADR-209)

G_INTEGRITY_MANIFEST 게이트의 핵심 구현체.
스크립트 직접 실행이 아닌 import 방식으로 run_release_gate.py에서 사용한다.

사용법 (import):
    from tools.generate_sha256sums import generate_sums, write_sums, verify_sums

사용법 (CLI):
    python tools/generate_sha256sums.py             # 생성 + 출력
    python tools/generate_sha256sums.py --verify    # 기존 파일 검증만
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMS_FILE = REPO_ROOT / "SHA256SUMS.txt"
MINISIG_FILE = REPO_ROOT / "SHA256SUMS.txt.minisig"

# SHA256SUMS.txt 자신은 재귀 해시에서 제외
_SELF_EXCLUDE: frozenset[str] = frozenset({"SHA256SUMS.txt"})

# 무시할 경로 접두사 (상대경로, Unix 슬래시 기준)
_EXCLUDE_PREFIXES = (
    ".git/",
    "__pycache__/",
    ".pytest_cache/",
    "out/",
    "dist/",
    "build/",
    "*.egg-info/",
    "literary_os.egg-info/",
)
_EXCLUDE_SUFFIXES = (".pyc", ".egg-info")


class VerifyResult(NamedTuple):
    matched: list
    mismatched: list
    missing: list


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _should_include(rel: str) -> bool:
    """상대 경로가 SHA256SUMS에 포함될지 결정."""
    if rel in _SELF_EXCLUDE:
        return False
    for prefix in _EXCLUDE_PREFIXES:
        if rel.startswith(prefix):
            return False
    for suffix in _EXCLUDE_SUFFIXES:
        if rel.endswith(suffix):
            return False
    return True


def _git_tracked_files(repo_root: Path) -> list:
    """git ls-files로 추적 파일 목록 반환. 실패/비git 시 전체 파일 폴백."""
    def _rglob_fallback() -> list:
        return sorted(
            f for f in repo_root.rglob("*")
            if f.is_file() and _should_include(
                str(f.relative_to(repo_root)).replace("\\", "/")
            )
        )
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=str(repo_root), timeout=30,
        )
        if result.returncode != 0:
            return _rglob_fallback()
        files = []
        for line in result.stdout.splitlines():
            rel = line.strip()
            if not rel:
                continue
            f = repo_root / rel
            if f.exists() and f.is_file():
                files.append(f)
        if not files:
            return _rglob_fallback()
        return sorted(files)
    except Exception:
        return _rglob_fallback()


def compute_file_hash(path: Path) -> str:
    """파일 SHA256 16진수 반환."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── 공개 API ─────────────────────────────────────────────────────────────────

def generate_sums(repo_root: Path = REPO_ROOT) -> dict:
    """git 추적 파일 전체의 {상대경로: sha256_hex} 반환.

    SHA256SUMS.txt 자신과 _EXCLUDE_PREFIXES 대상은 자동 제외.
    """
    files = _git_tracked_files(repo_root)
    result: dict = {}
    for f in files:
        rel = str(f.relative_to(repo_root)).replace("\\", "/")
        if not _should_include(rel):
            continue
        try:
            result[rel] = compute_file_hash(f)
        except (OSError, PermissionError):
            pass
    return result


def write_sums(repo_root: Path = REPO_ROOT) -> Path:
    """SHA256SUMS.txt 재생성 후 경로 반환."""
    sums = generate_sums(repo_root)
    output = repo_root / "SHA256SUMS.txt"
    lines = [f"{h}  {path}\n" for path, h in sorted(sums.items())]
    output.write_text("".join(lines), encoding="utf-8")
    return output


def verify_sums(repo_root: Path = REPO_ROOT) -> VerifyResult:
    """SHA256SUMS.txt와 실제 파일을 비교해 (matched, mismatched, missing) 반환."""
    sums_path = repo_root / "SHA256SUMS.txt"
    if not sums_path.exists():
        return VerifyResult(matched=[], mismatched=[], missing=["SHA256SUMS.txt"])

    recorded: dict = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "  " not in line:
            continue
        hash_val, rest = line.split("  ", 1)
        recorded[rest.strip()] = hash_val.strip()

    matched: list = []
    mismatched: list = []
    missing: list = []

    for rel_path, expected_hash in recorded.items():
        actual = repo_root / rel_path
        if not actual.exists():
            missing.append(rel_path)
        else:
            if compute_file_hash(actual) == expected_hash:
                matched.append(rel_path)
            else:
                mismatched.append(rel_path)

    return VerifyResult(matched=matched, mismatched=mismatched, missing=missing)


def check_minisig(repo_root: Path = REPO_ROOT) -> dict:
    """minisig 서명 파일 존재 여부 및 간이 검증 결과 반환."""
    sig = repo_root / "SHA256SUMS.txt.minisig"
    if not sig.exists():
        return {
            "present": False,
            "warn": "SHA256SUMS.txt.minisig 미존재 — minisign 키 발급 권고 (차단 아님)",
        }
    try:
        first_line = sig.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
        valid_fmt = first_line.startswith("untrusted comment:") or first_line.startswith(
            "trusted comment:"
        )
        return {"present": True, "valid_format": valid_fmt}
    except Exception as exc:
        return {"present": True, "valid_format": False, "error": str(exc)}


# ── CLI 엔트리 포인트 ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Literary OS SHA256SUMS 생성·검증 유틸리티"
    )
    parser.add_argument("--verify", action="store_true", help="생성 없이 기존 파일 검증만 수행")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="저장소 루트 경로")
    args = parser.parse_args()

    if args.verify:
        result = verify_sums(args.repo)
        sys.stdout.write(f"✅ matched:    {len(result.matched)}\n")
        sys.stdout.write(f"❌ mismatched: {len(result.mismatched)}\n")
        sys.stdout.write(f"   missing:   {len(result.missing)}\n")
        if result.mismatched:
            for p in result.mismatched[:10]:
                sys.stdout.write(f"  MISMATCH: {p}\n")
        sys.exit(0 if not result.mismatched and not result.missing else 1)
    else:
        out = write_sums(args.repo)
        result = verify_sums(args.repo)
        sys.stdout.write(f"SHA256SUMS.txt 생성 완료: {out}\n")
        sys.stdout.write(f"  항목 수: {len(result.matched) + len(result.mismatched)}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
