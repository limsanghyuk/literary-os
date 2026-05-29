"""V360 테스트 설정."""
import sys
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

collect_ignore = [
    "test_v329_nkg_schema.py",
    "test_v329_nkg_graph_store.py",
    "test_v329_scene_node_adapter.py",
    "test_v340_edge_infer.py",
    "test_v340_emotional_linker.py",
    "test_v340_pipeline_full.py",
    "test_gdap_pipeline.py",
    "test_gdap_blast_radius.py",
    "test_gdap_plan_gate.py",
]
