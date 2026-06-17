# T3 설계도 — 생성 본체 7-pass 입출력 계약·NKG 배선·실구현 (L4 v1.0)

**문서 ID**: LOS-T3-7PASS-IO-L4-V1.0-2026-06-17 · **기준**: 로컬 V781 `literary_system/generation/`(schema.py·pass_pipeline.py 골격) · **대상**: 저연산 개발 모드 · **ADR 제안**: ADR-242
**목적**: 4트랙 계획의 ★최대 빈칸(T3). V781은 계약(dataclass)+훅 골격뿐 — Pass1 단순복사·Pass2 STANDARD_ARC 템플릿·Pass3 slug "TBD". 본 문서가 각 Pass의 **입출력 계약 + NKG/일관성 배선 + 스텁→실체 포인트**를 명세해 loop-C가 개선할 *실체*를 공급한다.

## 0. 원칙 (불변)
- LLM-0: Pass1~3·6 = 결정론(LLM 미호출). 외부 LLM은 **Pass5 generate·Pass7 judge 훅 안에서만**(critic 경계).
- 데이터 소스: corpus_ko 455편 tri-store(ChromaDB·SceneFeature·NKG nkg.json). verbatim 비커밋.
- 계약은 V781 `schema.py`(WorkSpec/Beat/SceneBrief)를 **확장**(필드 추가)하되 하위호환.

## 1. 전체 데이터 흐름 (입출력 타입)
```
premise(dict) │ corpus priors
 └Pass1→ WorkSpec        (거시설계: 주제·갈등축·인물{name,role,want,flaw}·장르곡선)
 └Pass2→ List[Beat]      (인과비트: function·causal_parent·plant/payoff_motifs·target_tension)
 └Pass3→ List[SceneBrief](생성단위: slug·characters·targets·rag_refs빈칸)
 └Pass4→ SceneBrief.rag_refs   (corpus_ko 유사씬 정박)
 └Pass5→ SceneBrief.draft      (★loop-C 생성기)
 └Pass6→ SceneBrief.gate       (공식 구조 sanity)
 └Pass7→ SceneBrief.panel      (쌍대 판정 → loop-C 선호쌍)
```

## 2. Pass별 계약 + NKG 배선 + 실구현 포인트

### Pass1 — 거시설계 (premise → WorkSpec)
- **입력**: premise{title,genre,n_episodes,master_theme,conflict_axis,core_dilemma,characters[],arc_summary?}.
- **출력**: WorkSpec. **장르곡선 주입**: genre→FE-7/EXP-C 장르별 긴장곡선(`drama_genre_drse`)에서 곡선 로드(현 하드코딩 curve 대체).
- **스텁→실체**: 현재 premise 복사뿐. 실체 = (a) 인물 want/flaw 미입력 시 corpus 인물원형에서 추론, (b) n_episodes>1이면 `arc/series_arc_planner`로 시리즈 아크 산정 연결.
- **NKG 배선**: 없음(거시).

### Pass2 — 인과비트 (WorkSpec+motifs → List[Beat])
- **입력**: spec, motifs(DRSE 모티프사전 `motif_drse_v2`에서 작품 주제 연관 모티프 top-k).
- **출력**: Beat[]. function·pos·**causal_parent**(인과 사슬)·plant_motifs·payoff_motifs·target_tension(장르곡선 위치값).
- **스텁→실체**: 현 STANDARD_ARC 7비트 고정 → (a) n_episodes·장르별 비트 수 가변(`episode_planner` K값), (b) plant→payoff **거리 스케줄**을 `causal_plan/payoff_scheduler`로 산정(현 climax/resolution 고정 배정 대체).
- **NKG 배선**: payoff_motifs ↔ DRSE 잔향 사전(콜백 타이밍 climax_payoff 반영).

### Pass3 — 씬브리프 (★생성 단위 계약, 가장 중요)
- **입력**: spec, beats.
- **출력**: SceneBrief[]. **확장 스키마 제안**(schema.py 추가):
  - `slug`{location,time,int_ext} — 현 "TBD" → **corpus 장소 분포**에서 function별 빈출 장소 샘플.
  - `characters` — 현 names[:2~3] → **NKG co-occurrence(top_pairs)** 기반: 해당 function·갈등축에 맞는 인물 조합 선택.
  - `targets`{tension_band,conflict_intensity_min,callback_motifs} (유지) + **신규** `pov_character`·`knowledge_delta`(이 씬에서 누가 무엇을 알게 되나 — `world/knowledge_state_tracker` 연결).
- **스텁→실체**: 장소·인물·POV를 corpus/NKG 통계로 채움(현 고정 규칙 대체).

### Pass4 — RAG 정박 (SceneBrief → rag_refs)
- **계약**: `RetrieveFn: SceneBrief → List[str]`(참조 텍스트). **검색 키 = (dramatic_function, characters 역할, target_tension band)**.
- **NKG 배선**: ChromaDB ko_scenes 코사인 top-k를 **같은 function + 유사 인물구도**로 필터(무관 씬 정박 방지). 집 환경은 `e2e_pass5_home.py`의 emb_cache 인메모리 코사인 재사용(ChromaDB 불요).
- **출력**: brief.rag_refs = [scene_id…] + 텍스트(로컬 전용).

### Pass5 — 초안 생성 (★loop-C 생성기 자리)
- **계약**: `GenerateFn: (SceneBrief, rag_refs) → draft(str)`.
- **주입 컨텍스트**: brief.targets + rag_refs + **NKG 인물 상태**(temporal_coherence CharacterState·knowledge_delta) + 잔향(plant된 모티프).
- **배선**: 이 훅에 **loop-C로 학습되는 로컬 생성기**(Llama-3.2-3B/8B QLoRA)가 꽂힘. 미주입 시 stub. = 생성 절반과 학습 절반(V774 LoopCClosure)의 접점.

### Pass6 — 구조 게이트 (draft → gate, LLM-0)
- **계약**: draft + brief.targets → gate{pass:bool, R:float, violations:[]}.
- **실체**: LOSConstitution R + SceneFeature(conflict_intensity·tension) 산출 → brief.targets.tension_band 이탈·conflict_min 미달 검출. 공식=구조 sanity(품질 아님).

### Pass7 — 패널 판정 (draft vs ref → 선호쌍)
- **계약**: `JudgeFn: (draft, ref) → 'draft'|'ref'|'tie'`. ref = **(권고) 연속생성이면 실제 다음 씬**(NextEpisodeBench), 아니면 corpus 명작 씬.
- **NKG/품질 배선**: ref 선택 시 **품질 라벨(V775/V776)** 로 명작 우선. 판정 결과 (draft 패) → **loop-C 선호쌍**(V774 LoopCClosure 입력).

## 3. 교차-Pass 일관성 배선 (전편 단위)
- **temporal_coherence**(V313/322): Pass3 knowledge_delta·Pass5 인물상태를 회차 타임라인에 누적 → CoherenceViolation 검출.
- **causal_continuation**(V317): Pass2 plant → 후속 beat payoff 전파(미회수 payoff_debt 추적).
- 시리즈(n_episodes>1): Pass1 series_arc → 각 화 Pass2~7 반복, 화 간 상태 이월.

## 4. 검증 훅 (실구현 DoD)
- 단위: 각 Pass 입출력 타입 계약 테스트(스키마 왕복).
- 통합: premise→7pass→GenerationResult E2E(현 PassPipeline 확장), gate_issues·panel_win 집계.
- 실데이터: corpus_ko 1작품 seed로 Pass4 실 RAG + Pass7 실 판정 → loop-C 선호쌍 산출(V774 연결 확인).

## 5. 분업·범위
- **본 설계(나)**: 입출력 계약·NKG 배선·스키마 확장 명세(본 문서).
- **개발자(코드)**: schema.py 필드 확장 + pass_pipeline 실구현(통계 주입·NKG 연결) + 테스트. V774/775/776 패턴 동일.
- **데이터트랙(나)**: Pass4 검색키·Pass3 통계(장소·co-occurrence 분포)·품질라벨 공급.

## 6. 결론
T3는 "새 골격"이 아니라 **V781 골격의 각 Pass를 corpus_ko/NKG 통계로 채워 실체화**하는 것. Pass3 씬브리프(생성 단위)와 Pass5 생성기 자리가 핵심. 이게 채워져야 loop-C(V774)가 개선할 *대상*이 생기고, T1(실 GPU 라운드)의 ΔW가 의미를 갖는다.
