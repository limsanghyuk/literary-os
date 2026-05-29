# V585 설계도 — GraphRealAdapter

**ADR-044 | V585 | L1**

## 클래스 구조

```
GraphRealAdapter(BaseMigrationAdapter)
  __init__(path=None, mock=False)
  add_node(id, label, metadata) → None
  get_node(id) → Optional[GraphRecord]
  remove_node(id) → bool
  add_edge(id, src_id, dst_id, label, weight, metadata) → None
  get_edge(id) → Optional[GraphEdgeRecord]
  remove_edge(id) → bool
  neighbors(node_id, direction) → List[str]
  bfs(start_id, max_depth) → List[str]
  dfs(start_id, max_depth) → List[str]
  node_count() → int
  edge_count() → int
  save() → None
  load() → None
  check_connection() → bool
  apply(migration) → bool
  rollback(migration) → bool

GraphRecord(dataclass)
  id: str
  label: str
  metadata: Dict[str, Any]
  to_dict() / from_dict()

GraphEdgeRecord(dataclass)
  id: str
  src_id: str
  dst_id: str
  label: str
  weight: float = 1.0
  metadata: Dict[str, Any]
  to_dict() / from_dict()
```

## networkx-optional 패턴

```python
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
```

networkx 있으면: nx.DiGraph() 사용 (BFS/DFS/neighbors 위임)  
networkx 없으면: defaultdict(list) adjacency dict, 순수 Python BFS/DFS

## graph_ops 처리

```python
for op_dict in (migration.graph_ops or []):
    op = op_dict["op"]
    if op == "add_node":   self.add_node(**op_dict["node"])
    elif op == "add_edge": self.add_edge(**op_dict["edge"])
    elif op == "remove_node": self.remove_node(op_dict["node_id"])
    elif op == "remove_edge": self.remove_edge(op_dict["edge_id"])
```

## JSON 영속화

```json
{
  "nodes": [{"id":..., "label":..., "metadata":...}],
  "edges": [{"id":..., "src_id":..., "dst_id":..., "label":..., "weight":..., "metadata":...}]
}
```

## Gate G44 체크포인트 7개

1. import GraphRealAdapter, GraphRecord, GraphEdgeRecord
2. 인스턴스 생성, node_count()==0
3. add_node/add_edge/get_node/get_edge
4. neighbors(direction="out"/"in"/"both")
5. bfs/dfs 순회
6. JSON save/load via tempfile
7. rollback 검증 + HAS_NETWORKX=False fallback
