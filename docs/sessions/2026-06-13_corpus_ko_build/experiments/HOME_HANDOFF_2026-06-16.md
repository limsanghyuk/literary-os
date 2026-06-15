# 집 로컬 이어가기 핸드오프 (2026-06-16)

**목적**: 회사 세션 종료 → 집 로컬에서 동일 맥락으로 재개. 오늘의 데이터 작업 + **제품 비전·구현현황 재정렬**을 기록.

## 0. 오늘 한 일 (데이터 트랙, 모두 허브 push 완료)
1. **인코딩 결함 교정**: 소스 UTF-16을 utf-8로 읽어 생긴 모지바케 112편(25%) → `fix_encoding.py`(idempotent) 일괄 교정 → tri-store 전면 재처리.
2. **무결성 정식 입증**(`INTEGRITY_PROOF_2026-06-15.md`): 청크=임베딩=ChromaDB=**62,514 정확 일치**, 고아 0, features 36,291행/455작품, 이전 깨짐작(궁) 한국어 정상 회귀0. 미변환 1편(연애의목적.hwp 0바이트)만 정직 기록.
3. **NER LLM 폴백**(`NER_LLM_FALLBACK_RESULT.md`): NOCHAR 75→0, **인물 커버리지 100%**(455편/5,889인물). 궁·부산행·적도의남자 등 grounding 추출.
4. **README 권위정합**: V749/13.3.0 → **V761/v13.14.0/Phase E.2/11,079 테스트**.
- 허브 커밋: `eddc98b → d6a512a → fe52c68`.

## 1. ★오늘의 핵심 — 제품 비전·구현현황 재정렬 (대화로 확정)
### 북극성
**AI가 인간 작가팀처럼 자율적으로 문학을 생성**하는 기반. (V100대~V761이 그 인프라 구현.)

### 개발 2단계 순서 (사용자 명시 — 혼동 금지)
- **1단계(현재)**: 프롬프트·데이터를 주면 **전문 인간 작가팀 결과물 수준**으로 자율 생성해 보여주기. ← 지금 여기.
- **2단계(추후)**: 작가 협업점 = 사용자 수정-전파.
- → 사용자 개입 레이어 부재는 **누락이 아니라 의도된 후순위.** 먼저 만들지 말 것.

### 코드 구현 현황 (V761 실측 — "이미 로직 있다" 확인)
- **A. 계층 자율 생성 = 구현됨**: `arc/series_arc_planner`(V380, 16부작 아크→CausalPlotGraph) → `episode/episode_planner`(V392, 미시플롯 K 동적산정) + `microplot_matrix` → `orchestrators/sequence_planner`(V325, MacroArc→시퀀스·씬) → `episode/episode_structure_calculator`(V482, 1화 씬슬롯) → `longform_endurance_orchestrator`(V399)·`narrative_conductor`(V408). + 가상 작가팀 = `agents/director·editor·critic_agent` ensemble.
- **B. 일관성·전방 전파 토대 = 구현됨**: `coherence/temporal_coherence`(V313/322) · `causal_plan/causal_continuation_plan`(V317, PayoffPropagationReport) · `payoff_scheduler` · `world/knowledge_state_tracker.propagate_knowledge` · `render_loop/specialized_patch`(국소수술)·`closed_loop_render`(자기교정).
- **빈칸(2단계 과제) = 작가-편집 트리거 전파**: 현존 전파는 전부 시스템 내부 트리거(critic·전방 이어가기). 작가가 노드 수정→의존 downstream 무효화→재생성하는 human-edit 진입점은 미구현(의도적 후순위).

## 2. 현재 1단계의 진짜 척도·위치
- 척도 = **생성물 vs 실 한국명작 쌍대 승률**. 현 실측 = **2/4(막상막하, 아직 못 이김)** = loop-C 학습목표 baseline.
- 인프라(자율 작가팀 구조)는 섰고, 남은 1단계 과제 = **산출물 품질을 명작 수준까지 좁히기**.

## 3. 집에서 이어서 (다음 작업)
**우선(1단계 품질 격차):**
1. 명작 **베스트 씬 큐레이션**(임의 씬 아닌 명작의 강한 전환·climax씬) → 레퍼런스 풀 고도화.
2. **전편 단위 품질 척도 설계**(아크·인물 일관성·페이오프를 features+패널로 전편 평가) — 씬 leaf 측정 너머.
3. **대규모 반복 E2E**(작품 10편×씬 5+, 반복) → 승률 안정화 → DPO 본학습(E.4). ※로컬 필수(샌드박스 45초 한계).
4. DPO 선호쌍 누적(`dpo_pairs.jsonl` 오늘 17쌍) 확대.

**집 복원 주의(중요):**
- Drive `corpus_ko.zip`은 **인코딩 교정 전(stale)** → 교정본 재동기화 필수(아니면 모지바케 112편 재발).
- `.db`/ChromaDB는 FUSE 쓰기불가 → 로컬에서 `store_chroma.py`+`features.py`로 재빌드(emb_cache 313샤드 교정본 무손상).

## 4. 읽는 순서 (집 재개 시)
이 문서 → `INTEGRITY_PROOF_2026-06-15.md` → `SESSION_SUMMARY_2026-06-15.md` → `NER_LLM_FALLBACK_RESULT.md` → `DATA_INTEGRITY_NOTE.md`(갱신본).
메모리: `project_product_vision_generation_arch.md`(★비전·2단계·구현현황) · `project_hub_v761_phase_e2.md`.
