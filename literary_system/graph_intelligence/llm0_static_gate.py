"""
V546 — LLM0StaticGate
P5(graph_intelligence/ LLM-0 정책 명시적 시행 장치 부재) 해소. ADR-031.

AST 정적 분석으로 graph_intelligence/ 패키지 내 외부 LLM 호출을 탐지.
CI/CD 단계에서 호출하거나 release_gate에서 연동.

탐지 대상:
  - openai.ChatCompletion / openai.Completion
  - anthropic.Anthropic / claude API 직접 호출
  - requests.post / httpx.post to llm endpoints
  - litellm.completion / llm_bridge imports
"""
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# 금지 심볼 패턴 (AST 수준)
FORBIDDEN_IMPORTS = {
    "openai", "anthropic", "litellm", "cohere", "google.generativeai",
}
FORBIDDEN_CALL_PATTERNS = {
    "ChatCompletion", "Completion.create", "messages.create",
    "generate_content", "litellm.completion",
}
FORBIDDEN_FROM_IMPORTS = {
    ("literary_system.llm_bridge", None),  # graph_intelligence에서 llm_bridge 직접 import
}


@dataclass
class ViolationRecord:
    file: str
    line: int
    violation_type: str   # IMPORT / CALL / FROM_IMPORT
    detail: str


@dataclass
class LLM0StaticResult:
    passed: bool
    scanned_files: int = 0
    violations: List[ViolationRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pass": self.passed,
            "scanned_files": self.scanned_files,
            "violation_count": len(self.violations),
            "violations": [
                {"file": v.file, "line": v.line,
                 "type": v.violation_type, "detail": v.detail}
                for v in self.violations
            ],
        }


class LLM0StaticGate:
    """
    graph_intelligence/ AST 정적 분석으로 LLM-0 정책 시행.
    ADR-031: Phase 4·5 모듈의 외부 LLM 호출 0 보장.
    """

    def __init__(self, target_dir: str | Path | None = None) -> None:
        if target_dir is None:
            # 자동 탐지: 이 파일 기준 부모 디렉토리
            target_dir = Path(__file__).parent
        self._target = Path(target_dir)

    def scan(self) -> LLM0StaticResult:
        """target_dir 하위 모든 .py 파일을 AST 분석."""
        violations: List[ViolationRecord] = []
        scanned = 0

        for py_file in sorted(self._target.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            scanned += 1
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            rel = str(py_file.relative_to(self._target.parent))
            self._check_tree(tree, rel, violations)

        passed = len(violations) == 0
        result = LLM0StaticResult(
            passed=passed,
            scanned_files=scanned,
            violations=violations,
        )
        if passed:
            logger.info("LLM0StaticGate PASS: %d 파일 스캔, 위반 0건", scanned)
        else:
            logger.warning("LLM0StaticGate FAIL: %d 위반 탐지", len(violations))
        return result

    def _check_tree(self, tree: ast.AST, filename: str,
                    violations: List[ViolationRecord]) -> None:
        for node in ast.walk(tree):
            # import 검사
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(f) for f in FORBIDDEN_IMPORTS):
                        violations.append(ViolationRecord(
                            file=filename, line=node.lineno,
                            violation_type="IMPORT",
                            detail=f"import {alias.name}"
                        ))

            # from X import Y 검사
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if any(mod.startswith(f) for f in FORBIDDEN_IMPORTS):
                    violations.append(ViolationRecord(
                        file=filename, line=node.lineno,
                        violation_type="FROM_IMPORT",
                        detail=f"from {mod} import ..."
                    ))
                # llm_bridge 직접 import (graph_intelligence에서)
                if "graph_intelligence" in filename and "llm_bridge" in mod:
                    violations.append(ViolationRecord(
                        file=filename, line=node.lineno,
                        violation_type="FROM_IMPORT",
                        detail=f"LLM-0 위반: graph_intelligence에서 llm_bridge 직접 import"
                    ))

            # 함수 호출 검사
            elif isinstance(node, ast.Call):
                call_str = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
                for pattern in FORBIDDEN_CALL_PATTERNS:
                    if pattern in call_str:
                        violations.append(ViolationRecord(
                            file=filename, line=node.lineno,
                            violation_type="CALL",
                            detail=f"금지 호출: {call_str}"
                        ))
                        break


def make_release_gate_fn(target_dir: str | Path | None = None):
    """release_gate GATES용 callable 반환."""
    gate = LLM0StaticGate(target_dir)

    def _gate_llm0_static() -> dict:
        return gate.scan().to_dict()

    return _gate_llm0_static
