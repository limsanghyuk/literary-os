# ADR-018: CharacterInfluenceMatrix — CIM 아키텍처

**상태:** 채택 (V501~V504)
**결정자:** Chief System Principal Engineer, Chief Architect
**날짜:** 2026-05-17

## 결정

`literary_system/nie/character_influence_matrix.py`에 CIM 신설.

### 핵심 수학 구조
```
W[i][j] ∈ [-1, +1]       비대칭 영향력 행렬
B(A,B,C) = sign(W_AB)×sign(W_BC)×sign(W_CA)   구조적 균형
T(A,B,C) = 1 - B ∈ {0,2}                       삼각 긴장
PageRank: d=0.85, 양수 W만, 30 iter
```

### SparseCIM (M-N07)
- N>15: 자동 sparse 모드 활성
- |W|<0.10: 엣지 자동 컬링

### TopKTriangleFilter (M-N08)
- |T|≥1.5인 삼각형 중 top-50 heap
- N=20→C(20,3)=1140: heap으로 처리

### 5티어 (장기판)
```
장(將): PR≥0.80   차(車): 0.60≤PR<0.80
포(包): BC≥0.70   마·상: 0.30≤PR<0.60   졸: PR<0.30
```

## 결과
- Gap 4 (인물 영향 행렬 + 구조적 균형) 완전 해결
- TemporalCIM (V505+) 확장 기반
- PageRank 결과 → AMW 초기화 주입 가능
