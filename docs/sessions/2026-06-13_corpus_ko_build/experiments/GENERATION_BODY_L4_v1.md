# 생성 본체 — P4 orchestration 7패스 L4 명세 v1 (2026-06-13)

**목적**: 06-11 진단의 "남은 최대 기획" = *"무엇을 평가하나"가 아니라 "무엇을 생성하나"*. 의사코드 골격(L3) → **입출력 계약·NKG 배선·씬브리프 스키마가 박힌 L4 집행명세**. 이번 세션 검증 부품만 배선(추가 가정 없음).

## 중심 데이터 객체: SceneBrief (모든 패스가 주고받는 계약)
```json
{
  "scene_id":"work::ep::scene_no",
  "beat_id":"인과맵 비트 참조",
  "slug":{"location":"비무장지대/초소","time":"밤","int_ext":"실내"},
  "characters":["유시진","서대영"],          // NKG에서 해당 시점 생존·등장 인물
  "dramatic_function":"갈등촉발|상승|반전|해소|잔향",
  "targets":{                                  // F-24/25 장르곡선 + fitness_v2에서 산출
     "tension_band":[0.4,0.6],                 // 장르·정규위치별 T_ideal 구간
     "conflict_intensity_min":0.3,
     "callback_motifs":["군화","무전기"]       // DRSE 사전: 이 씬에서 회수할 기성 모티프
  },
  "rag_refs":["chroma:scene_id...", "..."],    // Pass4가 채움
  "draft":null, "gate":null, "panel":null      // Pass5~7이 채움
}
```

## 7패스 파이프라인 (각 패스 = 입력계약→출력계약)

**Pass 1 — 거시 설계(Premise/Arc)**
- IN: lorebook.core_philosophy(master_theme·conflict_axis·core_dilemma) + series_arc(F-12)
- OUT: `WorkSpec{theme, conflict_axis, dilemma, arc_beats[]}`
- NKG: 인물·관계 그래프 초기화(write).

**Pass 2 — 인과 비트맵(Causality/Beat)**
- IN: WorkSpec + macro_causality(trigger→resolution→**residue**, tragic_engine)
- OUT: `Beat[]{beat_id, causal_parent, function, expected_residue}` (회차/막 단위 비트시트)
- 검증연결: residue 필드 = DRSE 모티프 누적 계획(잔향 0.70 궤적과 정합).

**Pass 3 — 씬 브리프 생성(SceneBrief 발행)**
- IN: Beat[] + 장르 라벨 + **F-24/25 장르 긴장곡선 템플릿**(EXP-C 실측)
- OUT: `SceneBrief[]` (위 스키마, draft 이전까지 채움). tension_band = 장르·정규위치 곡선에서 조회.
- NKG: 각 씬 시점 등장인물·관계상태 read.

**Pass 4 — RAG 컨텍스트 조립(검색)**
- IN: SceneBrief
- OUT: SceneBrief.rag_refs += ChromaDB 유사 레퍼런스 씬(ko_scenes, cosine) + NKG 인물 상태 + **DRSE 사전 callback 후보**
- 검증연결: tri-store(11,724 벡터) 그대로 사용. callback_motifs = 기성 모티프 중 미회수분.

**Pass 5 — 씬 초안 생성(Draft)**
- IN: SceneBrief(+rag_refs)
- OUT: SceneBrief.draft = LLM-k 생성 씬 텍스트(brief·레퍼런스 조건부)
- 제약: 절대 레퍼런스 복제 금지(앵커는 품질 기준이지 복사원본 아님).

**Pass 6 — 공식 sanity 게이트(씬 단위)**  ← ②루프B 교훈 반영
- IN: SceneBrief.draft
- OUT: `gate{pass:bool, fail_reasons[]}`. **씬 단위 fitness 점수**(conflict_arc 존재·tension_band 부합·callback 반영)로 판정.
- FAIL → Pass5 재생성(**짧은 루프 A**). 절대점수 아님(구간 충족 여부).
- ★핵심: 공식을 **씬 입자도**로 적용 — 루프B 음성결과(작품수준 fitness를 단일 씬에 적용 불가)를 구조적으로 해결.

**Pass 7 — 패널 정련(Refinement)**  ← 보상 신호
- IN: 게이트 통과 draft + 동일 dramatic_function의 실제 레퍼런스 씬
- OUT: `panel{accept:bool, pairwise_pref, refine_note}` + **선호쌍 로그**
- 검증연결: 패널 73%(만장일치 82%) POC 승격. 쌍대·레퍼런스 앵커·이질 앙상블.
- NKG: 확정 씬의 인물 상태 변화 write(다음 씬 Pass3 입력).

## 학습 루프 결선 (씬 입자도로 통일)
- **짧은 A**: Pass6 FAIL→Pass5 재생성.
- **중간 B(교정판)**: Pass7 **씬쌍 선호** → **씬-스코어러**(씬 단위 fitness) 재가중. ※작품수준 아님(②에서 작품수준은 40%로 실패 확인).
- **긴 C**: Pass7 선호쌍 누적 → 보상모델 → 생성기(Pass5) LoRA/RLHF (F-43~55, 쌍대 보상).

## 불변식 (설계 게이트)
쌍대만 · 실제 대본 앵커 · 생성기(Pass5)≠심판(Pass7) 모델군 · 객관 명성 주기 캘리브레이션 · Gold/고위험은 인간 작가 체크포인트.

## DoD (소넷 집행 기준)
1. `orchestration/scene_brief.py` — SceneBrief 스키마 + 검증(pydantic).
2. `orchestration/pass1~7_*.py` — 각 패스 IN/OUT 계약 픽스처 통과.
3. Pass4 = 기존 rag/hybrid_retriever + ChromaDB 결선. Pass6 = 씬-fitness(F-04 씬판). Pass7 = panel_judge.py(POC 승격).
4. 통합 스모크: SceneBrief 1건 → 7패스 → 확정 씬 + NKG 갱신 + 선호쌍 로그 1건.

## 미해결(정직)
- 씬-스코어러(Pass6 씬 단위 fitness)의 성분·가중은 미검증 — 작품수준 fitness_v2(conflict+thematic)를 씬판으로 내리는 캘리브레이션 필요(다음 실측).
- Pass5 생성 품질 자체는 미측정(코퍼스는 평가용; 생성 POC는 Phase E 과제).
- 패널 보상의 씬쌍 노이즈 → 다중 평가·만장일치 가중 필요(②).
