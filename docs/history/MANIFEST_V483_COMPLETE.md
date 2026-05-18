# Literary OS V483 — COMPLETE Manifest

**버전:** V483  
**기준선:** V481 Hotfix  
**릴리즈 일자:** 2026-05-16  
**패키지:** `literary_os_v483_COMPLETE.zip`

---

## 테스트 결과

```
4511 passed, 18 skipped — 0 FAILED
```

신규 테스트: +59개 (V482: 27개, V483: 32개)

---

## 신규 모듈

| 모듈 | 경로 | 설명 |
|------|------|------|
| EpisodeStructureCalculator | `literary_system/episode/episode_structure_calculator.py` | 60분 한국 드라마 타임라인 계산기 |
| TreeNode / TreeNodeBuilder | `literary_system/schemas/tree_node.py` | 서사 계층 트리 노드 스키마 v1 |
| FractalPlotTreeBuilder | `literary_system/longform/fractal_plot_tree.py` | max_depth=4 재귀 구조 생성기 |
| KoreanCadencePlanner | `literary_system/prose/korean_cadence_planner.py` | 한국 드라마 문체 리듬 플래너 |

## 수정 사항

| 대상 | 수정 내용 |
|------|---------|
| `finetune/model_eval_harness.py` | BLEU smoothing: any(p==0)→return 0 제거, epsilon 치환 |
| `docs/adr/ADR-014_scene_necessity.md` | SceneNecessity 정책 공식 문서화 |

---

**LITERARY OS V483 — RELEASED**  
4511 PASSED / 0 FAILED — 2026-05-16
