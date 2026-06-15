# 개발자 보고 — 다음 단계 계획 (2026-06-15)

**수신**: 개발자(limsanghyuk) · **발신**: 데이터·검증 트랙(본 모드) · **기준**: 허브 `0eb9841`(V761/v13.14.0) + corpus_ko 455편.

## 0. 한 줄
**코드트랙(V761·Phase E.2 LLM-1 Critic 완료)과 데이터트랙(corpus_ko 455편)이 수렴.** 개발자가 데이터 부재로 못 한 "절대검증①"을 본 세션이 실데이터로 완료(생성 vs 실명작 2/4). 다음=**E.3(UI)·E.4(RLAIF) 병렬 → E.5(Exit)로 Phase E 종료.**

## 1. Phase E 종료 시점 (질의 응답)
**SP 순서**: E.0(무결성)✅ → E.1(코퍼스50)✅ → E.2(LLM-1 Critic 핵심)✅ → **E.3(UI MVP)·E.4(RLAIF) 병렬** → **E.5(Exit Gate) = Phase E 종료.**
- 현재 위치: **E.2 완료(V761)**. 잔여 비중 ≈ E.3 20% + E.4 20% + E.5 10% = Phase E의 약 50%.
- E.5 Exit 후 → Phase F(LLM-1.5) → G(LLM-2) → H(LLM-2.5).
- **E.3 리스크(문서 명시)**: 작가 베타 모집 실패 시 UI MVP 검증 불가. → E.4(RLAIF)를 병렬·선행 가능(데이터·자동평가만으로 진행).

## 2. 본 세션 산출 (코드트랙에 직접 기여)
- **corpus_ko 455편**(영화~105 + 드라마 신규 미생·시그널·커피프린스·풍문·국제시장·암살 등 편입). ChromaDB 32,813(scene)·SceneFeature·NKG. → **G_LLM1_SAFETY(코퍼스≥50) 대폭 충족, E.4 RLAIF 학습 데이터 확보.**
- **★절대검증① 완료**(`e2e_pass5_local.py` 실데이터): Pass4 실RAG(ChromaDB 32,813) + Pass7 실명작 풀(13,725씬). 결과 **Pass6 4/4·R 0.559·생성 vs 실명작 2/4**.
  - 개발자 06-15 샌드박스판(레퍼런스=열화자기) 생성 4/4 압승 → **실명작 레퍼런스로 2/4 하락 = 진짜 시험 작동**. 현 LLM-0 생성은 한국명작과 막상막하(아직 못 이김) = **E.4 loop-C 학습 목표 정량 baseline 확보**.
- 공식 R 패턴(arc·tension 바닥) **4번째 독립 재확인** → "공식=구조게이트/패널=품질보상" 설계 재확정(arbitration.py 운용 타당).

## 3. 다음 단계 계획 (권고)
### 즉시 (E.4 RLAIF 선행 — 데이터만으로 가능)
1. **E2E 다씬·다작품 반복 측정**(개발자 로컬): 본 세션 단일실측(2/4, n=4)을 **작품 10편×씬 5 이상**으로 확대해 생성 vs 실명작 승률을 안정화 → loop-C 격차 정량. ※ 샌드박스는 455편 풀 스캔이 45초 초과로 불가, 로컬 필수.
2. **선호쌍 수집 → DPO/RLAIF**(E.4): Pass7 패널의 (생성 패·실명작 승) 쌍을 보상 데이터로 → 생성기 LoRA. 승률 2/4→상승이 목표 지표.
3. **신규 60편 임베딩 완료**: 본 세션은 변환·파싱까지(scenes 편입). `embed.py`+`store_chroma.py`로 ChromaDB 편입 → Pass4 RAG 풀 확대.

### 병렬 (E.3 UI — 작가 모집 의존)
4. **작가 GT 1차 라운드**: human_gt.py(V750)·alignment_monitor(G_LLM1_ALIGNMENT≥0.80) 준비됨. 작가 1~5명 섭외 → Critic↔인간 일치율 실측(현재 미투입).
5. **UI MVP 3-zone**(Claude Design): E2E 결과(생성·레퍼런스·공식R·패널)를 작가 검수 화면으로.

### 보강 (병행 가능)
6. **NKG 인물 시리즈 NER**(CHAR_NER_PROPOSAL): 드라마 166편 NOCHAR → 화자위치+헤딩제외+LLM 시리즈폴백. Pass3/4 인물 주입 입력.
7. **드라마 메타GT(시청률·수상)** 취합 → 드라마 FE-7 개통.
8. 미변환 3편(공작·암살 대형PDF 일부)·rar 1편 도구 확보.

## 4. 데이터 인계 (집/로컬)
Drive `corpus_ko.zip`(456M)+`Scripts.zip` 업로드 완료. **단 scene_features.db(0B)·chroma_export(잘림) 손상** → `DATA_INTEGRITY_NOTE.md`대로 `features.py`+`store_chroma.py` 재구축(emb_cache 무손상). 신규 60편 포함 시 재변환·재임베딩.

## 5. 결론
**Phase E.2 완료·검증 수렴 완료. E.5가 Phase E 종료점.** 즉시 권고 = **E.4 RLAIF 선행**(E2E 반복으로 loop-C 격차 정량 → DPO). E.3 UI는 작가 모집과 병렬. 본 세션이 그 출발 데이터(455편)와 baseline(2/4)을 제공함.
