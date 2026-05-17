# ADR-021: TemporalCIM — 시간 차원 인물 관계 진화

**상태:** 채택 (V505~V508)
**결정자:** Chief Architect
**날짜:** 2026-05-17

## 결정

`literary_system/nie/temporal_cim.py`에 TemporalCIM 신설.

### 핵심 수학
```
W[t][i][j] = η·W[t-1][i][j] + (1-η)·(W[t-1][i][j] + lr·delta)
           = W[t-1] + (1-η)·lr·delta
η = 0.92 (memory decay)
window = 5 (최근 5화 평균)
```

### 기능
- `update(t, i, j, delta)`: 에피소드 t의 관계 업데이트
- `get_recent_window(t)`: 최근 5화 평균 CIM 반환
- `flashback_compare(current_t, flashback_t)`: 회상 신 비교

### 적용
- 씬 분석 후 delta_W 추출 → TemporalCIM.update()
- 회상 신: flashback_compare() → 양수=관계 강화, 음수=약화
- window view → NIL Step 2 삼각 긴장 입력

## 결과
- Gap 4 시간 차원 (M-N03) 해결
- W[t][i][j] 역사 보존 → 에피소드별 관계 추적
