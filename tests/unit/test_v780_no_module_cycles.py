"""test_v780 — gates/ 순환(모듈레벨) 0 보장 (V780, ADR-240). TC01~05."""
import importlib.util, sys
from pathlib import Path
_REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("_pf", _REPO/"tools"/"run_preflight.py")
_pf = importlib.util.module_from_spec(_spec); sys.modules["_pf"]=_pf; _spec.loader.exec_module(_pf)

def test_tc01_module_level_builder_exists():
    assert hasattr(_pf, "_build_module_level_deps")
def test_tc02_no_module_level_cycles():
    cycles = _pf._find_cycles(_pf._build_module_level_deps())
    assert cycles == [], f"모듈레벨 순환 잔존: {cycles}"
def test_tc03_lazy_imports_excluded():
    # 함수 내부 지연 import는 모듈레벨 그래프에 미포함
    deps = _pf._build_module_level_deps()
    ap = "literary_system.gates.auto_promotion_gate"
    assert ap not in deps.get(ap, set())   # 자기참조(함수내) 제외됨
def test_tc04_full_graph_still_has_lazy():
    # 전체 그래프(연결성용)는 지연 import 유지(영향분석 보존)
    full = _pf._build_dep_graph()
    ap = "literary_system.gates.auto_promotion_gate"
    assert ap in full.get(ap, set())       # 함수내 자기 import는 전체 그래프엔 존재
def test_tc05_connectivity_unaffected():
    # 고립 검출은 별도 로직 → 영향 없음
    orphans = _pf._find_orphans()
    assert isinstance(orphans, list)
