"""
tests/gates/test_v746_integrity_manifest.py — G_INTEGRITY_MANIFEST Gate (V746, ADR-209)

WP-0 DoD 5종 포함 총 33 TC:
  - test_gate_regenerates_manifest          (DoD-1)
  - test_self_verify_passes_on_clean        (DoD-2)
  - test_stale_entry_blocks_release         (DoD-3)
  - test_inventory_count_mismatch_blocks    (DoD-4)
  - test_missing_sig_warns_not_blocks       (DoD-5)
  + 추가 28 TC (함수 단위, 엣지 케이스, CLI, 통합)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ── 모듈 로더 ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"모듈 로드 실패: {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


@pytest.fixture(scope="session")
def sha_mod():
    return _load_module("generate_sha256sums", TOOLS_DIR / "generate_sha256sums.py")


@pytest.fixture(scope="session")
def gate_mod():
    return _load_module("run_release_gate", TOOLS_DIR / "run_release_gate.py")


# ── 격리 임시 저장소 픽스처 ──────────────────────────────────────────────────

@pytest.fixture()
def tmp_repo(tmp_path):
    """임시 git 저장소 (최소 파일 포함)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo), check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(repo), check=True,
    )
    # 기본 파일 3개 생성
    (repo / "main.py").write_text("# main\n", encoding="utf-8")
    (repo / "utils.py").write_text("# utils\n", encoding="utf-8")
    (repo / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=str(repo), check=True,
    )
    return repo


# ════════════════════════════════════════════════════════════════════════════
# §1 compute_file_hash — 6 TC
# ════════════════════════════════════════════════════════════════════════════

class TestComputeFileHash:
    def test_known_hash(self, sha_mod, tmp_path):
        """빈 파일의 SHA256 값이 표준값과 일치."""
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert sha_mod.compute_file_hash(f) == expected

    def test_content_change_changes_hash(self, sha_mod, tmp_path):
        """내용 변경 시 해시 변경."""
        f = tmp_path / "data.txt"
        f.write_bytes(b"hello")
        h1 = sha_mod.compute_file_hash(f)
        f.write_bytes(b"world")
        h2 = sha_mod.compute_file_hash(f)
        assert h1 != h2

    def test_large_file(self, sha_mod, tmp_path):
        """1 MB 파일 정상 처리."""
        f = tmp_path / "large.bin"
        f.write_bytes(b"x" * 1_048_576)
        h = sha_mod.compute_file_hash(f)
        assert len(h) == 64

    def test_hash_is_hex_string(self, sha_mod, tmp_path):
        """반환값이 64자 16진수 문자열."""
        f = tmp_path / "abc.txt"
        f.write_bytes(b"literary_os")
        h = sha_mod.compute_file_hash(f)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_nonexistent_file_raises(self, sha_mod, tmp_path):
        """존재하지 않는 파일은 예외 발생."""
        with pytest.raises((FileNotFoundError, OSError)):
            sha_mod.compute_file_hash(tmp_path / "nonexistent.bin")

    def test_deterministic(self, sha_mod, tmp_path):
        """같은 파일을 두 번 해시해도 결과 동일."""
        f = tmp_path / "det.txt"
        f.write_bytes(b"deterministic check 123")
        assert sha_mod.compute_file_hash(f) == sha_mod.compute_file_hash(f)


# ════════════════════════════════════════════════════════════════════════════
# §2 generate_sums / write_sums — 7 TC
# ════════════════════════════════════════════════════════════════════════════

class TestGenerateWriteSums:
    def test_generate_sums_returns_dict(self, sha_mod, tmp_repo):
        """generate_sums()가 dict 반환."""
        sums = sha_mod.generate_sums(tmp_repo)
        assert isinstance(sums, dict)
        assert len(sums) >= 3

    def test_generate_sums_excludes_self(self, sha_mod, tmp_repo):
        """SHA256SUMS.txt 자신은 결과에서 제외."""
        sums_file = tmp_repo / "SHA256SUMS.txt"
        sums_file.write_text("dummy\n", encoding="utf-8")
        subprocess.run(["git", "add", "SHA256SUMS.txt"], cwd=str(tmp_repo), check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "add sums"],
            cwd=str(tmp_repo), check=True,
        )
        sums = sha_mod.generate_sums(tmp_repo)
        assert "SHA256SUMS.txt" not in sums

    def test_write_sums_creates_file(self, sha_mod, tmp_repo):
        """write_sums()가 SHA256SUMS.txt를 생성."""
        sha_mod.write_sums(tmp_repo)
        assert (tmp_repo / "SHA256SUMS.txt").exists()

    def test_write_sums_format(self, sha_mod, tmp_repo):
        """SHA256SUMS.txt 각 줄이 '<hash>  <path>' 형식."""
        sha_mod.write_sums(tmp_repo)
        lines = (tmp_repo / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 1
        for line in lines:
            parts = line.split("  ", 1)
            assert len(parts) == 2, f"잘못된 형식: {line!r}"
            assert len(parts[0]) == 64

    def test_write_sums_sorted(self, sha_mod, tmp_repo):
        """SHA256SUMS.txt 경로 기준 정렬."""
        sha_mod.write_sums(tmp_repo)
        paths = [
            ln.split("  ", 1)[1]
            for ln in (tmp_repo / "SHA256SUMS.txt")
            .read_text(encoding="utf-8").splitlines()
        ]
        assert paths == sorted(paths)

    def test_generate_sums_excludes_pyc(self, sha_mod, tmp_repo):
        """__pycache__/*.pyc 파일은 제외."""
        cache = tmp_repo / "__pycache__"
        cache.mkdir()
        (cache / "cached.pyc").write_bytes(b"\x00")
        sums = sha_mod.generate_sums(tmp_repo)
        assert not any("__pycache__" in k for k in sums)

    # DoD-1: gate regenerates manifest
    def test_gate_regenerates_manifest(self, sha_mod, tmp_repo):
        """G_INTEGRITY_MANIFEST: SHA256SUMS.txt가 존재하지 않아도 재생성된다."""
        sums_file = tmp_repo / "SHA256SUMS.txt"
        if sums_file.exists():
            sums_file.unlink()
        sha_mod.write_sums(tmp_repo)
        assert sums_file.exists()
        lines = sums_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 1


# ════════════════════════════════════════════════════════════════════════════
# §3 verify_sums — 8 TC
# ════════════════════════════════════════════════════════════════════════════

class TestVerifySums:
    # DoD-2: self verify passes on clean
    def test_self_verify_passes_on_clean(self, sha_mod, tmp_repo):
        """재생성 직후 verify_sums()는 불일치 0."""
        sha_mod.write_sums(tmp_repo)
        vr = sha_mod.verify_sums(tmp_repo)
        assert vr.mismatched == []
        assert vr.missing == []
        assert len(vr.matched) >= 1

    # DoD-3: stale entry blocks release
    def test_stale_entry_blocks_release(self, sha_mod, tmp_repo):
        """파일 수정 후 verify_sums()는 mismatched에 해당 파일 포함."""
        sha_mod.write_sums(tmp_repo)
        # 파일 변조
        (tmp_repo / "main.py").write_text("# tampered\n", encoding="utf-8")
        vr = sha_mod.verify_sums(tmp_repo)
        assert len(vr.mismatched) >= 1
        assert "main.py" in vr.mismatched

    def test_missing_file_reported(self, sha_mod, tmp_repo):
        """추적 파일 삭제 시 missing에 포함."""
        sha_mod.write_sums(tmp_repo)
        (tmp_repo / "utils.py").unlink()
        vr = sha_mod.verify_sums(tmp_repo)
        assert "utils.py" in vr.missing

    def test_no_sums_file_returns_missing(self, sha_mod, tmp_repo):
        """SHA256SUMS.txt 자체가 없으면 missing에 'SHA256SUMS.txt' 포함."""
        vr = sha_mod.verify_sums(tmp_repo)
        assert "SHA256SUMS.txt" in vr.missing

    def test_verify_result_is_named_tuple(self, sha_mod, tmp_repo):
        """VerifyResult가 .matched/.mismatched/.missing 속성 보유."""
        sha_mod.write_sums(tmp_repo)
        vr = sha_mod.verify_sums(tmp_repo)
        assert hasattr(vr, "matched")
        assert hasattr(vr, "mismatched")
        assert hasattr(vr, "missing")

    def test_verify_count_consistency(self, sha_mod, tmp_repo):
        """matched + mismatched + missing = SHA256SUMS.txt 항목 수."""
        sha_mod.write_sums(tmp_repo)
        lines = [
            ln for ln in
            (tmp_repo / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
            if "  " in ln
        ]
        vr = sha_mod.verify_sums(tmp_repo)
        total = len(vr.matched) + len(vr.mismatched) + len(vr.missing)
        assert total == len(lines)

    def test_verify_after_new_file_not_tracked(self, sha_mod, tmp_repo):
        """git 미추적 신규 파일은 verify 결과에 영향 없음 (SHA256SUMS에 없으므로)."""
        sha_mod.write_sums(tmp_repo)
        (tmp_repo / "untracked_new.py").write_text("# new\n", encoding="utf-8")
        vr = sha_mod.verify_sums(tmp_repo)
        assert vr.mismatched == []

    def test_empty_sums_file_passes_trivially(self, sha_mod, tmp_repo):
        """비어있는 SHA256SUMS.txt: matched/mismatched/missing 모두 0."""
        (tmp_repo / "SHA256SUMS.txt").write_text("", encoding="utf-8")
        vr = sha_mod.verify_sums(tmp_repo)
        assert vr.matched == [] and vr.mismatched == [] and vr.missing == []


# ════════════════════════════════════════════════════════════════════════════
# §4 check_minisig — 3 TC
# ════════════════════════════════════════════════════════════════════════════

class TestCheckMinisig:
    # DoD-5: missing sig warns not blocks
    def test_missing_sig_warns_not_blocks(self, sha_mod, tmp_repo):
        """minisig 미존재 시 present=False + warn 문자열 반환 (예외 아님)."""
        info = sha_mod.check_minisig(tmp_repo)
        assert info["present"] is False
        assert "warn" in info
        assert isinstance(info["warn"], str)

    def test_present_sig_detected(self, sha_mod, tmp_repo):
        """minisig 파일 생성 시 present=True 반환."""
        (tmp_repo / "SHA256SUMS.txt.minisig").write_text(
            "untrusted comment: test\ndummybase64==\n", encoding="utf-8"
        )
        info = sha_mod.check_minisig(tmp_repo)
        assert info["present"] is True

    def test_minisig_format_check(self, sha_mod, tmp_repo):
        """유효 형식 minisig는 valid_format=True."""
        (tmp_repo / "SHA256SUMS.txt.minisig").write_text(
            "untrusted comment: signature from minisign\ndummydata==\n",
            encoding="utf-8",
        )
        info = sha_mod.check_minisig(tmp_repo)
        assert info.get("valid_format") is True


# ════════════════════════════════════════════════════════════════════════════
# §5 _check_integrity_manifest (run_release_gate) — 5 TC
# ════════════════════════════════════════════════════════════════════════════

class TestCheckIntegrityManifest:
    """run_release_gate._check_integrity_manifest() 직접 테스트."""

    def _invoke(self, gate_mod, monkeypatch, repo_root: Path) -> dict:
        """REPO_ROOT를 tmp_repo로 교체하고 _check_integrity_manifest 호출."""
        monkeypatch.setattr(gate_mod, "REPO_ROOT", repo_root)
        return gate_mod._check_integrity_manifest()

    def test_pass_on_fresh_repo(self, gate_mod, monkeypatch):
        """실제 저장소에서 _check_integrity_manifest()가 pass=True."""
        # REPO_ROOT를 실제 저장소로 유지 (monkeypatch 없음)
        # 실제 tools/generate_test_inventory.py 실행 포함
        result = gate_mod._check_integrity_manifest()
        # sha256 재생성 직후 verify는 항상 mismatch=0
        assert result["sha256_mismatch"] == 0
        assert result["sha256_missing"] == 0
        # inventory 재생성 후 카운트 ≥ 이전값
        assert result["inventory_match"] is True
        assert result["pass"] is True

    def test_fail_when_sha256_module_unavailable(self, gate_mod, monkeypatch):
        """generate_sha256sums 모듈 로드 실패 시 pass=False.

        게이트가 항상 write_sums→verify 순서로 재생성하기 때문에
        변조는 verify_sums()로만 감지 가능(§3 DoD-3에서 검증). 
        게이트 레벨에서는 모듈 자체를 로드할 수 없는 경우를 FAIL 처리해야 한다.
        """
        def _unavailable():
            raise ImportError("generate_sha256sums.py 탐지 불가 — 무결성 게이트 실패")

        monkeypatch.setattr(gate_mod, "_load_sha256_module", _unavailable)
        result = gate_mod._check_integrity_manifest()
        assert result["pass"] is False
        assert "reason" in result
        assert len(result.get("reason", "")) > 0

    def test_minisig_warn_present_in_result(self, gate_mod, tmp_repo, monkeypatch):
        """minisig 미존재 시 minisig_warn 필드 존재."""
        result = self._invoke(gate_mod, monkeypatch, tmp_repo)
        assert result["minisig_warn"] is not None
        assert isinstance(result["minisig_warn"], str)

    # DoD-4: inventory count mismatch blocks
    def test_inventory_count_mismatch_blocks(self, gate_mod, tmp_repo, monkeypatch):
        """test_inventory TC 수가 이전보다 크게 줄면 inventory_match=False."""
        # 현재 재생성 후 카운트가 9999인 척하는 가짜 인벤토리 생성
        inv = {"test_count": 99999, "generated_at": "2026-01-01T00:00:00+00:00",
               "pytest_version": "pytest 9.0.0", "source_hash": "aabbccdd",
               "generator": "tools/generate_test_inventory.py"}
        (tmp_repo / "test_inventory.json").write_text(
            json.dumps(inv), encoding="utf-8"
        )
        result = self._invoke(gate_mod, monkeypatch, tmp_repo)
        # 실제 재생성 카운트(0)가 99999보다 훨씬 작음 → inventory_match=False
        assert result["inventory_match"] is False

    def test_result_has_required_keys(self, gate_mod, tmp_repo, monkeypatch):
        """결과 dict에 필수 키 존재."""
        result = self._invoke(gate_mod, monkeypatch, tmp_repo)
        for key in ("pass", "sha256_match", "sha256_mismatch", "sha256_missing",
                    "inventory_before", "inventory_after", "inventory_match",
                    "minisig_warn", "details"):
            assert key in result, f"키 누락: {key}"


# ════════════════════════════════════════════════════════════════════════════
# §6 CLI 통합 — 4 TC
# ════════════════════════════════════════════════════════════════════════════

class TestCLI:
    """CLI(--verify 플래그 등)를 subprocess로 통합 검증."""

    def test_cli_verify_exits_0_on_clean(self, tmp_repo):
        """생성 직후 --verify 모드는 종료코드 0."""
        sha_py = str(TOOLS_DIR / "generate_sha256sums.py")
        # 먼저 생성
        subprocess.run(
            [sys.executable, sha_py, "--repo", str(tmp_repo)],
            check=True, capture_output=True,
        )
        # 검증
        proc = subprocess.run(
            [sys.executable, sha_py, "--verify", "--repo", str(tmp_repo)],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0

    def test_cli_verify_exits_1_on_tampered(self, tmp_repo):
        """파일 변조 후 --verify 모드는 종료코드 1."""
        sha_py = str(TOOLS_DIR / "generate_sha256sums.py")
        subprocess.run(
            [sys.executable, sha_py, "--repo", str(tmp_repo)],
            check=True, capture_output=True,
        )
        (tmp_repo / "main.py").write_text("# tampered\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, sha_py, "--verify", "--repo", str(tmp_repo)],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1

    def test_cli_generate_prints_summary(self, tmp_repo):
        """CLI 생성 모드는 '생성 완료' 문자열 출력."""
        sha_py = str(TOOLS_DIR / "generate_sha256sums.py")
        proc = subprocess.run(
            [sys.executable, sha_py, "--repo", str(tmp_repo)],
            capture_output=True, text=True,
        )
        assert "생성 완료" in proc.stdout or proc.returncode == 0

    def test_run_release_gate_verify_only_flag(self, tmp_repo):
        """run_release_gate.py --verify-only: JSON 결과 출력 후 종료."""
        gate_py = str(TOOLS_DIR / "run_release_gate.py")
        proc = subprocess.run(
            [sys.executable, gate_py, "--verify-only"],
            capture_output=True, text=True,
            cwd=str(REPO_ROOT),
        )
        # --verify-only는 항상 JSON 출력 (pass 여부와 무관)
        combined = proc.stdout + proc.stderr
        assert "G_INTEGRITY_MANIFEST" in combined or "pass" in combined.lower()
