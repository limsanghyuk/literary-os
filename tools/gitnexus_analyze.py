"""GitNexus Equivalent Analyzer v2 — AST 기반 심볼/관계 분석 (V589)"""
import ast
import os
from pathlib import Path
from collections import defaultdict

ROOT = Path("/tmp/literary-os-v589")
SRC  = ROOT / "literary_system"
TESTS = ROOT / "tests"

SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules"}

symbols = {}          # key -> "class"|"method"|"function"|"test_fn"
relationships = set() # (from_mod, rel_type, to)
execution_flows = set()

class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, mod_name: str):
        self.mod = mod_name
        self._class_stack = []

    def visit_ClassDef(self, node):
        key = f"{self.mod}.{node.name}"
        symbols[key] = "class"
        execution_flows.add(key)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node):
        if self._class_stack:
            key = f"{self.mod}.{self._class_stack[-1]}.{node.name}"
            symbols[key] = "method"
        else:
            key = f"{self.mod}.{node.name}"
            t = "test_fn" if node.name.startswith("test_") else "function"
            symbols[key] = t
            if t == "function":
                execution_flows.add(key)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node):
        for alias in node.names:
            relationships.add((self.mod, "IMPORTS", alias.name))

    def visit_ImportFrom(self, node):
        if node.module:
            relationships.add((self.mod, "IMPORTS", node.module))
            for alias in node.names:
                relationships.add((self.mod, "USES", alias.name))

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            relationships.add((self.mod, "CALLS", node.func.attr))
        elif isinstance(node.func, ast.Name):
            relationships.add((self.mod, "CALLS", node.func.id))
        self.generic_visit(node)


def scan_dir(path: Path):
    for f in sorted(path.rglob("*.py")):
        if any(s in f.parts for s in SKIP):
            continue
        rel = f.relative_to(ROOT)
        mod = ".".join(rel.with_suffix("").parts)
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(f))
            SymbolVisitor(mod).visit(tree)
        except SyntaxError:
            pass

scan_dir(SRC)
scan_dir(TESTS)

# V588/V589 신규 심볼
v589_new = sorted(k for k in symbols if "health_monitor" in k.lower() or "hybridretrieverv2" in k.lower())
v588_new = sorted(k for k in symbols if "query_interface" in k.lower() and "test_" not in k)

total_sym  = len(symbols)
total_rel  = len(relationships)
total_flow = len(execution_flows)

print("=" * 55)
print("  GitNexus Equivalent Analysis — release_v589")
print("=" * 55)
print(f"  총 심볼(Symbols):      {total_sym:>7,}")
print(f"    클래스:              {sum(1 for v in symbols.values() if v=='class'):>7,}")
print(f"    메서드:              {sum(1 for v in symbols.values() if v=='method'):>7,}")
print(f"    함수:                {sum(1 for v in symbols.values() if v=='function'):>7,}")
print(f"    테스트 함수:         {sum(1 for v in symbols.values() if v=='test_fn'):>7,}")
print(f"  총 관계(Relationships):{total_rel:>7,}")
print(f"    IMPORTS:             {sum(1 for r in relationships if r[1]=='IMPORTS'):>7,}")
print(f"    USES:                {sum(1 for r in relationships if r[1]=='USES'):>7,}")
print(f"    CALLS:               {sum(1 for r in relationships if r[1]=='CALLS'):>7,}")
print(f"  실행흐름(Exec Flows):  {total_flow:>7,}")
print()
print(f"  [V588 신규] QueryInterface 심볼: {len(v588_new)}개")
print(f"  [V589 신규] HealthMonitor 심볼:  {len(v589_new)}개")
print()

# 상위 클러스터
print("  주요 클러스터 (literary_system.*)")
print("  " + "-" * 44)
pkg_cnt = defaultdict(int)
for k, t in symbols.items():
    parts = k.split(".")
    if len(parts) >= 3 and parts[0] == "literary_system":
        pkg_cnt[parts[1]] += 1
for pkg, cnt in sorted(pkg_cnt.items(), key=lambda x: -x[1])[:12]:
    bar = "█" * (cnt // 20)
    print(f"  {pkg:<28} {cnt:>5}  {bar}")

print()
print("  V589 신규 심볼 목록:")
for s in v589_new[:20]:
    print(f"    {s}")

print()
print("=" * 55)
print(f"  인덱스명: release_v589")
print(f"  기준:     v9.4.0 / 47 Gates / ADR-001~050")
print("=" * 55)
