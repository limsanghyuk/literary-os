# ADR-027: CIM-NarrativeGraph 단일 동기화 채널

Status: Accepted

## 문제
CharacterInfluenceMatrix(CIM)와 NarrativeGraphStore가 독립적으로 운영되어
CIM의 PageRank 결과가 NarrativeGraph에 반영되지 않음 (P1).
이중 업데이트 오버헤드 발생 (P2).

## 결정
GraphSyncOrchestrator를 통한 단일 양방향 동기화 채널 확립.
- CIM PageRank → NarrativeGraph CharacterNode.metadata["cim_influence"]
- NarrativeGraph 관계 엣지 weight → CIM weight_matrix
- sync() 단일 호출로 원자적 처리

## 근거
P1·P2를 V546에서 해소. Phase 6 Stage A 클린업 범위.
