# 전수 분석 — 문학 생성 도메인 깊이 + LangChain/LangGraph/LangSmith 대체 구조 (2026-06-17)

**기준**: 허브 `da9be83`(V780/v13.33.0) · literary_system **87개 패키지** 전수 조사 · 로컬 V781 generation/ 포함.

## 1. 문학 생성(소설·시나리오)이라는 도메인의 깊이
자율 문학 생성은 "LLM 호출 체인"이 아니라 **서사 공학(narrative engineering)**이다. 87개 패키지 중 도메인 본체:

| 층 | 패키지 | 역할(작법의 코드화) |
|---|---|---|
| 거시 구조 | `arc`(series_arc_planner·causal_plot_graph) · `episode`(episode_planner K값·microplot_matrix·structure_calculator) · `longform`(16화 endurance) | 화→거시/미시 플롯→씬 산정 |
| 인과·복선 | `causal_plan`(causal_continuation·payoff_scheduler) · `drse`(잔향·모티프 사전) · `nkg`(인물·관계·co-occurrence 그래프) | plant→payoff 스케줄·콜백 |
| 일관성 | `coherence`(temporal_coherence·CharacterState) · `world`(knowledge_state_tracker) | 회차 간 인물 상태·지식 추적 |
| 미시 문체 | `prose`(rhythm_rewriter) · `style`(style_dna) · `emotion` · `physics`(긴장) · `trajectory`(곡선) | 대사 리듬·문체·감정·긴장 |
| 품질 판단 | `constitution`(LOSConstitution 공식 게이트) · `critic`(5축 패널·alignment·arbitration) · `quality`(2축 라벨·판별게이트) | 구조 sanity + 쌍대 품질 |
| 학습 | `learning`(loop_c·reward_model·rlaif) · `finetune`(QLoRA·GPU 3모드) · `rlhf` | 선호쌍→DPO 생성기 진화 |

→ **범용 LLM 프레임워크엔 이 중 0개도 없다.** 이건 한국 드라마/영화 작법을 코드·공식·그래프로 옮긴 도메인 자산이다.

## 2. LangChain / LangGraph / LangSmith ↔ 우리 모델 대응 (전수)
| 스택 | 일반 역할 | 우리 대응 패키지 | 사용 여부 |
|---|---|---|---|
| **LangChain** | 체인·프롬프트·모델 어댑터·툴콜·RAG | `adapters`/`adapters_live`/`llm_bridge`(LLM I/O) + `rag`/`retrieval`/`reference`(RAG) + `agents`/`ensemble`(멀티에이전트) | 🟡 `langchain-core`/`langchain-anthropic`은 **선택적 extra만**, 코드 import 0 |
| **LangGraph** | 상태형 그래프 오케스트레이션(사이클·분기) | `orchestrators`(13모듈: narrative_conductor·longform_endurance·sequence_planner…) + `generation/pass_pipeline`(7-pass) + `arc`·`episode`·`causal_plan`·`coherence`(서사 상태머신) | ❌ 미사용, 자체 구현 |
| **LangSmith** | 트레이싱·평가·모니터링·데이터셋 | `trace`(self_learning_collector·trace_dataset_store) + `ops`(trace_context) + `evaluation`·`validation`(human_gt·pairwise)·`quality`·`proof`·`audit` + `critic`(alignment_monitor·llm1_metrics 비용) | ❌ 미사용, 자체 구현 |

코어 의존성은 **networkx·pydantic·RestrictedPython** 셋뿐. langgraph·langsmith는 의존성에 아예 없음.

## 3. 왜 자체 대체인가 (설계 근거)
1. **LLM-0 주권("판단은 로컬")**: 작법·품질 판단이 외부 모델/프레임워크에 갇히면 통제·진화 불가.
2. **결정성·검증성**: 공식 게이트·번호 ADR·named 게이트를 파이프라인에 직접 박음 — 범용 그래프 추상은 이 정밀 제약을 표현 못 함.
3. **점진 완화(LLM-0→1→2.5)**: 외부 LLM을 단계적·경계적으로만 허용. 프레임워크 종속이면 단계 통제 불가.

## 4. "보다 진보된 방식인가" — 정직한 축별 평가
| 축 | 평가 |
|---|---|
| 문학 도메인 깊이 | ★**우리가 압도적 진보** — 서사공학 코드화. 범용 스택엔 0(빈 캔버스) |
| 판단 주권·결정성·검증 | ★**우리가 진보** — 공식·게이트·경계. 범용 스택은 블랙박스 의존 |
| 범용 인프라 성숙도·생태계·툴링 | **범용 스택 우위** — LangSmith UI·LangGraph 분산실행·커뮤니티. 우리는 재구현 비용·생태계 부재 |
| 관측·디버깅 편의 | **LangSmith 우위**(즉시 UI). 우리 `trace/`는 맞춤이나 UI 없음 |
| 확장·운영 자동화 | 대등~범용 우위(우리는 KEDA/RunPod 자체 구현 중) |

**결론(정직)**:
- 범용 "LLM 앱 플러밍"으로는 *더 진보가 아니다* — 그쪽이 성숙·생태계 우위이고, 우리는 **의도적으로 그 영역에서 경쟁하지 않는다**.
- 그러나 **"자율 문학 생성 + 통제 가능한 품질 판단 + 주권적 학습"이라는 목표 도메인에서는 우리 설계가 더 진보적이고 목적적합**하다.
- 핵심 차별: 범용 프레임워크는 *무엇을 생성/평가하는지 모른다*(plumbing만 제공). 우리는 **작법·일관성·품질을 도메인 지식으로 코드화**했다. 그 대가로 범용 인프라를 재구현하는 유지비를 진다 — **주권 vs 생태계의 의도된 트레이드오프**.

## 5. 정직한 리스크·권고
- 자체 trace/orchestration의 유지비·관측 UI 부재 → 코어 비종속을 지키되 **LangSmith류 관측을 옵트인**으로 얹는 선택 고려 가능.
- 생성 본체(T3 7-pass)가 아직 빈칸 → **도메인 깊이가 "구현"으로 완성돼야 진보성이 실증**된다. 현재는 *구조·평가·학습 기계가 앞서고 생성 실체가 따라오는 중*. 진보성의 마지막 증명 = T3 생성 본체 실구현 + loop-C 폐회로 실가동(T1).
