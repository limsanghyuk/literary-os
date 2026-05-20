#!/usr/bin/env python3
"""
Literary OS — CLI 레퍼런스 자동 생성 도구 (V587 SP-γ)

docs/user/reference.md 를 Gate/ADR/모듈 목록 기반으로 자동 갱신.

사용법:
    python tools/gen_cli_reference.py               # docs/user/reference.md 갱신
    python tools/gen_cli_reference.py --check        # 갱신 필요 여부 확인만
    python tools/gen_cli_reference.py --stdout       # 파일 저장 없이 출력
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / "docs" / "user" / "reference.md"


def collect_gates() -> list[dict]:
    """release_gate.py 에서 실제 GATES 목록 수집."""
    sys.path.insert(0, str(ROOT))
    from literary_system.gates.release_gate import GATES
    return [{"id": g[0], "desc": g[1]} for g in GATES]


def collect_adr_index() -> list[str]:
    """docs/adr/INDEX.md 에서 ADR 목록 수집."""
    index_path = ROOT / "docs" / "adr" / "INDEX.md"
    if not index_path.exists():
        return []
    lines = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ADR-") and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                lines.append(f"- **{parts[0]}**: {parts[-1]}" if len(parts) >= 3 else f"- {parts[0]}")
    return lines


def collect_version() -> str:
    """pyproject.toml 에서 버전 추출."""
    pyproject = ROOT / "pyproject.toml"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            return line.split("=")[1].strip().strip('"')
    return "unknown"


def generate_reference() -> str:
    """reference.md 전체 내용 생성."""
    version = collect_version()
    gates = collect_gates()
    adrs = collect_adr_index()

    gate_table = "\n".join(
        f"| `{g['id']}` | {g['desc'][:70]}{'...' if len(g['desc']) > 70 else ''} |"
        for g in gates
    )

    adr_list = "\n".join(adrs) if adrs else "_(INDEX.md 없음)_"

    return f"""# Literary OS — Gate & ADR 레퍼런스 (v{version})

자동 생성 기준일: {__import__('datetime').date.today()} (gen_cli_reference.py)

---

## Release Gate 목록 ({len(gates)}개)

| Gate ID | 설명 |
|---------|------|
{gate_table}

---

## ADR 목록

{adr_list}

---

## API 요약

자세한 API 설명은 [docs/user/reference.md](reference.md) 의 수동 작성 섹션을 참조하세요.

### 핵심 진입점

```python
# 전체 45 Gates 실행
from literary_system.gates.release_gate import run_release_gate
r = run_release_gate()
print(r["gates_passed"], "/", r["total_gates"])  # 45 / 45

# fast-path (L0+L1)
from literary_system.gates.release_gate import run_release_gate_tiered
r = run_release_gate_tiered(tiers=["L0", "L1"])

# E2E 산문 게이트
from literary_system.gates.e2e_prose_gate import gate_e2e_prose
result = gate_e2e_prose(mock=True)
print(result.checkpoints_passed, "/", result.total_checkpoints)  # 6 / 6

# 샘플 드라마 생성
python examples/sample_drama/generate.py
```
"""


def main():
    parser = argparse.ArgumentParser(description="Literary OS CLI 레퍼런스 자동 생성")
    parser.add_argument("--check", action="store_true", help="갱신 필요 여부 확인만")
    parser.add_argument("--stdout", action="store_true", help="stdout 출력 (파일 저장 없음)")
    args = parser.parse_args()

    content = generate_reference()

    if args.stdout:
        sys.stdout.write(content)
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if content.strip() == current.strip():
            sys.stdout.write("reference.md: UP-TO-DATE\n")
        else:
            sys.stdout.write("reference.md: NEEDS UPDATE\n")
            sys.exit(1)
        return

    OUTPUT.write_text(content, encoding="utf-8")
    sys.stdout.write(f"reference.md 갱신 완료: {len(content)}자, {len(generate_reference().splitlines())}행\n")


if __name__ == "__main__":
    main()
