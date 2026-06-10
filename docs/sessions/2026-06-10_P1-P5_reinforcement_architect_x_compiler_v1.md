# P1~P5 보강 종합 — 수석 아키텍트 × 수석 컴파일러 교차 리뷰 v1.0 (2026-06-10)

**기준선**: HEAD `2116218` (V745 재인덱싱 정합) · 선행: P1-P5 완성도 감사(06-07) · MASTER §7
**방법**: 두 페르소나의 독립 리뷰 → 쟁점 교차 → 합의안. 페르소나 정의:
- **수석 아키텍트(A)**: 개념 무결성·경계·확장성·진화 방향. "이 설계가 5 Phase 뒤에도 유효한가"
- **수석 컴파일러(C)**: 구현 가능성·결정성·테스트 가능성·비용. "이 설계를 내일 코드로 옮길 수 있는가"
**목적**: ① P1~P5 갭의 구체 보강(설계 수준 상향) ② 교차 리뷰로 발견한 문제점+해결책 ③ V745 이후 장기 진화 로드맵의 골격(성급함 방지 장치 포함)

═══════════════════════════════════════════
## §1. 전제 갱신 — 감사(06-07) 이후 변한 것
═══════════════════════════════════════════
1. **P1 사실상 해소**: 개발자가 06-10 SP-E.0 직접 실행 (`8d0edc7`: SHA256SUMS 재생성 stale 971→3859, test_inventory 10,788, tools/generate_sha256sums.py 추가, V745 정합 / `2116218`: GitNexus 재인덱싱). **잔여 = 서명(.sig 재생성, 개발자 키)·release_gate 내 G_INTEGRITY_MANIFEST 상시 게이트화·CI hook.**
2. **P2 입수 경로 구체화**: 대본집 전자책 확인 — 비밀의 숲(리디)·우리들의 블루스(리디/알라딘)·우영우(예스24, 전자책 개별확인). 미생 미확인 → 대체 후보 필요. 씬 3~5개 전사로 Mode 2 1차 가동 가능.
3. **검증 방법론 확정**: 레퍼런스 기반 프로토콜(Mode 2 우선·순환 0 / Mode 1 블라인드). POC가 'LLM 회상 레퍼런스 무효'를 실증.
4. **키 상태**: OpenAI만 가용. 비용 설계는 OpenAI 단일 기준으로.

═══════════════════════════════════════════
## §2. P1 보강 — 무결성 (L4 마감)
═══════════════════════════════════════════
**[A]** 무결성은 '실행 완료'가 아니라 '재발 불가능 구조'가 목표. 일회성 재생성은 stale의 재발을 막지 못한다.
**[C]** 동의. 단 CI가 없는 1인 로컬 환경에서 'pre-commit hook 강제'는 우회가 너무 쉬움 — release_gate 통과 시점 강제가 현실적.

**합의 보강안 (P1-R)**:
| ID | 항목 | 내용 |
|---|---|---|
| P1-R1 | G_INTEGRITY_MANIFEST 상시화 | release_gate.py 마지막 단계에 ①SHA256SUMS 재생성 ②자기검증(전 파일 해시 일치) ③test_inventory 재생성+카운트 일치 — 하나라도 실패 시 릴리즈 차단 |
| P1-R2 | 서명 체계 | minisign(또는 ssh-keygen -Y) 채택. 개발자 로컬 비밀키 1개·공개키는 레포 커밋. SHA256SUMS.txt.minisig만 재서명. GPG는 과중 — 기각 |
| P1-R3 | 매니페스트 단일성 | SHA256SUMS는 release_gate 산출물로만 생성(수동 생성 금지 주석 명기). generate_sha256sums.py는 release_gate가 호출하는 라이브러리로 격하 |
| P1-R4 | Exit 기준 | `python release_gate.py --verify-only`가 클린 환경에서 PASS + .minisig 검증 PASS |

═══════════════════════════════════════════
## §3. P2 보강 — 데이터 깊이 + GT (최대 병목의 설계 마감)
═══════════════════════════════════════════
### 3.1 피처테이블 정본 스키마 (P2-R1, DDL)
**[C]** 트라이스토어 시범은 ad-hoc 스키마였다. 정본 DDL 없이는 공식 검증 규모화가 매번 마이그레이션 비용을 낸다.
**[A]** provenance(출처·신뢰등급·전사자)와 rights(verbatim=false 강제)를 스키마 수준에서 박아야 — 게이트가 아니라 제약(constraint)으로.

```sql
-- scene_feature 정본 v1.0 (SQLite, 트라이스토어 피처 축)
CREATE TABLE work (
  work_id TEXT PRIMARY KEY,           -- 'secret_forest'
  title TEXT NOT NULL, writer TEXT, genre_group TEXT,
  source_path TEXT NOT NULL CHECK(source_path IN ('A_public','B_legal_script')),
  rights_note TEXT NOT NULL           -- 열람 근거 (대본집 ISBN / KMDB 등)
);
CREATE TABLE scene (
  scene_id TEXT PRIMARY KEY,          -- 'secret_forest_e01_s03'
  work_id TEXT NOT NULL REFERENCES work(work_id),
  episode INTEGER, scene_idx INTEGER,
  synopsis TEXT NOT NULL,             -- 구조 요약(전사 아님)
  verbatim_stored INTEGER NOT NULL DEFAULT 0 CHECK(verbatim_stored = 0),  -- 불변 제약
  provenance TEXT NOT NULL,           -- 'ebook_transcribe:2026-06-10:dev' 등
  trust_tier TEXT NOT NULL CHECK(trust_tier IN ('gold','silver','auto')),
  UNIQUE(work_id, episode, scene_idx)
);
CREATE TABLE scene_feature (          -- 13필드 SceneFeature + 확장
  scene_id TEXT PRIMARY KEY REFERENCES scene(scene_id),
  conflict_level REAL, energy REAL, motif_density REAL, curiosity REAL,
  tension REAL, emotion_valence REAL, emotion_arousal REAL,
  info_reveal REAL, agency_shift REAL, plant_count INTEGER, payoff_count INTEGER,
  pacing REAL, necessity REAL,
  feature_version TEXT NOT NULL,      -- 추출기 버전(공식 재현성)
  annotator TEXT NOT NULL,            -- 'llm:gpt-4o' | 'human:dev' | 'hybrid'
  agreement REAL                      -- 검수 일치율(있을 때)
);
CREATE TABLE plant_payoff (           -- DRSE/복선 GT
  pp_id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id TEXT NOT NULL REFERENCES work(work_id),
  plant_scene TEXT NOT NULL REFERENCES scene(scene_id),
  payoff_scene TEXT REFERENCES scene(scene_id),   -- NULL=미회수(부채)
  motif TEXT NOT NULL, strength REAL
);
CREATE INDEX idx_scene_work ON scene(work_id, episode);
```
- **불변 원칙**: `verbatim_stored=0` CHECK — 원문 저장은 스키마가 거부. 전사 원문은 로컬 비커밋 폴더(`local_transcripts/`, .gitignore)에만.

### 3.2 전사 SOP (P2-R2 — 전자책 → 분석 입력)
**[C]** 새 병목은 전사 노동. 표준화 없으면 씬마다 품질이 흔들린다.
1. 씬 선정: 1화 내 ①오프닝 훅 ②중반 전환 ③클라이맥스 직전 — 공식이 변별해야 할 에너지 스펙트럼을 커버하는 3씬 우선.
2. 전사 양식: 씬헤딩/지문/대사 구분 유지, 씬당 메타(등장인물·직전상태·거시목표) 기록 — Mode 1 생성 조건과 동일 포맷.
3. 저장: 원문 → `local_transcripts/`(비커밋). 허브 커밋은 scene/scene_feature 행 + synopsis만.
4. 검수: LLM 1차 피처 추출 → 개발자 스팟 체크(13필드 중 3필드 무작위) → agreement 기록.

### 3.3 GT 3층 구조 정식화 (P2-R3)
**[A]** '인간 GT 미설계' 갭은 레퍼런스 프로토콜로 대체됐지만, 층위가 문서마다 흩어져 있다. 정본 한 줄:
| GT 층 | 정답원 | 사용 검증 | 상태 |
|---|---|---|---|
| GT-1 명작 레퍼런스 | 실제 대본 씬(평단·시청 acclaim) | Mode 2(공식), Mode 1(생성) | **현행 주력** |
| GT-2 다중에이전트 패널 | 3~4 페르소나 블라인드 합의(일치율 보고 의무) | Mode 1 판정, Stage4 독자 대행 | 가동(OpenAI) |
| GT-3 인간 작가 | 작가 베타 블라인드 | 최종 절대 검증(G_VALUE_PROOF) | 차후(섭외 시 승격) |

═══════════════════════════════════════════
## §4. P3 보강 — Stage3~6 구체 설계 + DRSE 전환
═══════════════════════════════════════════
**공통 규약(사전등록)**: 각 Stage는 실행 전 ①가설 ②지표 ③임계 ④N ⑤제외 기준을 본 문서 또는 후속 문서에 커밋(사후 임계 조정 금지). 미달 공식 = '재보정 후보' 표시, 2회 연속 미달 = '폐기 후보'(§6 공식 생애주기).

| Stage | 공식군 | 입력 | GT | 지표·임계(사전등록) | 가동 조건 |
|---|---|---|---|---|---|
| 3 | Longform(scene_necessity·payoff_debt·attention_economy·agency·voice) | 회차 단위 씬 시퀀스(Gold 1작품 전 회차) | plant_payoff 테이블(실제 회수 여부)·씬 삭제 실험(necessity: 해당 씬 제거 시 후속 정합 붕괴 여부를 다중에이전트 판정) | payoff_debt vs 실제 미회수 일치 F1≥0.6 / necessity 상위·하위 10% 분리 AUC≥0.7 | Gold 1작품 회차 전사(B 경로) |
| 4 | Trajectory·reader_simulator | 씬 시퀀스 | **수정**: 시청자 리뷰·평점은 씬 단위 정렬 불가(작품 단위 교란) → GT-2 독자 페르소나 패널의 씬별 uncertainty/pull 설문으로 대체. 실 독자 지표는 Phase F로 이연 | simulator 출력 vs 패널 중앙값 ρ≥0.4 | OpenAI 가용(즉시 가능) |
| 5 | NIE(CIM·tension)·emotion·coherence | Gold 씬+인물 그래프 | 전사 시 기록한 인물·긴장 곡선 라벨(GT-1) + 패널 교차 | tension 곡선 vs 라벨 DTW 거리 백분위≤30% / CIM 방향 일치≥70% | Gold 2작품 |
| 6 | Prose/Style·Constitution 종합 | 생성물 vs 명작 | Mode 1 블라인드(GT-2) → GT-3 승격 | 종합점수가 블라인드 선호를 ρ≥0.5로 예측 | Mode 1 가동 후 |

**DRSE BGE-M3 전환 설계 (P3-R2)**:
- 인터페이스: `EmbeddingProvider` 프로토콜(`embed(texts)->ndarray`, `dim`, `provider_id`) — gemini-embedding(검증 완료 0.71)·BGE-M3(로컬 sentence-transformers)·OpenAI text-embedding-3-small(폴백) 3구현.
- 게이트 G_EMB_PARITY: BGE-M3가 동일 복선 검증셋에서 gemini 대비 잔향 탐지 ρ 90% 이상 재현 시 정본 승격(로컬=비용 0·키 독립).
- 캐시: scene_id+provider_id+model_rev 키로 임베딩 디스크 캐시(재실행 비용 0).
- **[C] 주의**: BGE-M3는 로컬 GPU/CPU 부하 — 1인 개발 장비에서 178편 배치 가능성 먼저 소규모 벤치(10씬) 후 확정.

═══════════════════════════════════════════
## §5. P4 보강 — 코어 구현명세(L4) 골격 + SP-E.2 버전맵
═══════════════════════════════════════════
**[A]** L4 전체를 지금 쓰는 것은 시기상조(검증 결과가 인터페이스를 바꾼다). 그러나 '명세 템플릿+모듈 경계+버전맵'은 지금 고정 가능하고, 고정해야 저연산 개발 모드가 움직인다.
**[C]** 동의 + 한 가지 강제: 모든 신규 모듈은 기존 부품(NKG·Critic·RAG·학습 부품 다수 실재 — 06-05~06 알고리즘 문서 §배선 참조)에 **어댑터로 접속**하며 신설은 인터페이스가 증명될 때만.

**모듈 경계 (5개, literary_system/ 하위)**:
| 모듈 | 책임 | 접속(기존) | 신규 인터페이스 |
|---|---|---|---|
| orchestration/ | 7패스 생성 파이프라인 조율 | generation 부품·los_constitution | `Orchestrator.run(brief)->EpisodeDraft` |
| critic/ | 5축 평가(LLM-1 보조) | surface_scorer·physics 공식군 | `Critic.evaluate(scene,ctx)->AxisScores` |
| rag_context/ | NKG+트라이스토어 컨텍스트 빌드 | drse_engine·vector store | `ContextBuilder.build(scene_brief)->Context` |
| learning/ | 개입·평가→학습신호(DPO 페어) | manuscript_learner(합성 제거) | `SignalCollector.collect(event)->TrainingPair` |
| validation/ | 공식 하니스 상설화 | tools/formula_validation/* 승격 | `Harness.run(stage_id)->Report` |

**명세 템플릿(모듈당 1문서, SP-E.2에서 작성)**: ①공개 인터페이스(시그니처·계약) ②의존(기존 모듈 정확 경로) ③에러·폴백 ④단위테스트 목록(케이스명 선기재) ⑤Gate 연결 ⑥V버전 할당.
**SP-E.2 버전맵(골격)**: V750 validation/ 상설화 → V752 rag_context/ → V754 critic/(LLM-1 게이트 5종) → V756 orchestration/ → V758 learning/ → V760 E.2 Exit(일치율 측정 개시). *번호는 제안 — 개발 모드가 실측으로 조정.*

═══════════════════════════════════════════
## §6. P5 보강 — UI·개입→학습신호 데이터플로
═══════════════════════════════════════════
**[A]** P5의 본질은 화면이 아니라 **개입 이벤트의 학습신호화** — UI는 그 수집기다.
**이벤트 스키마(정본)**: `InterventionEvent {event_id, ts, scene_id, type: edit|reorder|reject|accept|regenerate|annotate, before_hash, after_hash, axis_hint(옵션: 어느 축 불만), free_note}` → learning/SignalCollector가 DPO 페어로 변환(before=rejected, after=chosen).
**컴포넌트 명세(3-zone 상세는 기존 blueprint 유지, 추가 3건)**: ①ScenePanel(상태: draft/under_review/accepted, 액션 6종=이벤트 타입) ②CritiqueOverlay(5축 점수+공식 근거 표시 — 공식의 설명가능성 자산화) ③TimelineMap(payoff_debt 시각화 — 미회수 복선 잔액).
**[C]** Claude Design 실 prototype은 데이터·검증 후로 유지(감사 순서 6 불변). 단 이벤트 스키마만은 P4 learning/과 동시 고정해야 후행 재작업이 없다.

═══════════════════════════════════════════
## §7. 교차 리뷰 발견 — 문제점 7 + 해결책
═══════════════════════════════════════════
| # | 문제(발견자) | 해결책(합의) |
|---|---|---|
| 1 | **공식 생애주기 부재**(A): 검증 미달 공식의 처리 절차가 없음 → 부채 영구화 | 상태기계 도입: candidate→validated→recalibrate→deprecated. 2회 연속 미달=deprecated 후보, los_constitution 가중 0 처리. 원장(formula_ledger.md)에 이력 |
| 2 | **임계 사후조정 위험**(C): Stage 임계가 결과 후 조정되면 검증 무의미 | §4 사전등록 규약 + 변경은 별도 커밋·사유 의무 |
| 3 | **LLM-1 '일치율≥0.80' 정의 모호**(C): 무엇과 무엇의 일치인지 미정 | 정의 고정: critic 공식 점수 상하위 4분위 분류 vs LLM 판정의 Cohen's κ≥0.6 + 방향 일치≥0.80, 씬 N≥100 |
| 4 | **GT 이중화 미흡**(A): GT-2 패널이 전부 OpenAI면 단일 프로바이더 편향 | 페르소나는 유지하되 temperature·모델(4o/4o-mini) 교차 + 일치율 보고 의무. 키 복구 시 프로바이더 교차로 승격 |
| 5 | **정본 데이터 이중 소스**(C): corpus_seed JSON과 트라이스토어가 따로 존재 | §3 DDL을 정본으로, corpus_seed는 read-only 시드로 격하(마이그레이션 단방향) |
| 6 | **버스팩터=1**(A): 서명키·LLM키·전사물이 개발자 단일점 | 키 백업 SOP(오프라인 1부)·전사물 로컬+개인 클라우드 2부·허브는 구조 데이터만이라 유실 시 재전사 가능 |
| 7 | **비용 모델 부재**(C): Stage4·Mode1은 LLM 다회 호출 — 무계획 실행 시 키 소진 재발 | 실행 전 비용 상한 사전 계산(예: Mode 1 씬당 4o 평가 3회×2arm≈$0.15) + 하니스에 cost_cap 파라미터·도달 시 중단 |

═══════════════════════════════════════════
## §8. V745 이후 장기 진화 로드맵 (가정) — 성급함 방지 장치 내장
═══════════════════════════════════════════
**[A] 원칙 선언**: 개발자의 장기 구상은 정당하다. 그러나 전이 조건을 '버전 번호·일정'으로 두면 성급해진다. **전이는 오직 증거(Exit Gate PASS)로만** — capability-gated, not calendar-gated.

```
[현재] V745 + SP-E.0 완료
  │
  ├─ E-검증기 (V746~V760, LLM-1 진입 전 관문) ★지금 여기
  │   증거: Mode2 공식 on 명작 PASS → Stage3~6 순차 → 공식 생애주기 1회전
  │   Exit: ~25공식 중 validated≥15 / deprecated 처리 완료 / 트라이스토어 정본화
  │
  ├─ Phase E 본대 (V761~V795, LLM-1) — 기존 EFG 기획 유지
  │   E.2 critic/ 5게이트 · E.3 UI · E.4 RLAIF / Exit: κ 기반 일치율(§7-3) 3개월
  │
  ├─ Phase F (V796~V875, LLM-1.5) — 코퍼스 200·Critic 전체 AI·생성 초안(안1)
  │   추가 Exit(신설 제안): 실 독자 지표 1종 확보(Stage4 GT 승격)
  │
  ├─ Phase G (V876~V955, LLM-2.0~2.5 + 사업화) — 기존 기획 유지
  │
  └─ Phase H 스케치 (V956~, LLM-3?: 자율 학습 루프 — 모델이 자기 공식을 재보정)
      ※ 의도적으로 스케치만. 구체화 조건: G.2 자율루프 안전 게이트 1년 무사고
      ※ A·C 합의: 지금 H를 설계하는 것은 §7-2(사전등록 위반)와 같은 오류 —
         미래 설계는 그 직전 Phase의 증거 위에서만
```
**성급함 방지 장치 3종**: ①모든 Phase 전이=Exit Gate 증거 커밋 의무 ②역행 가능(LLM 완화는 degradation path 보유) ③신규 공식·모듈은 검증 계획 없이 머지 금지(G_FORMULA_VALIDATION, 기존 원칙 재확인).

═══════════════════════════════════════════
## §9. 실행 순서 (보강 반영 재산정)
═══════════════════════════════════════════
1. **[개발자] 전자책 1권 구매+3씬 전사**(P2 SOP §3.2) — 모든 검증의 관문, 오늘 가능
2. **[본 모드] Mode 2 실행**(공식 on 실제 씬, 순환 0) + §3.1 DDL 적용 트라이스토어 정본화
3. **[본 모드] Stage4 패널 검증**(OpenAI, 비용 상한 §7-7) — 데이터 불요라 병렬 가능
4. **[개발 모드] P1-R1~R4**(release_gate 상시 게이트+minisign) — 소규모
5. **[본 모드] SP-E.2 모듈 명세 5문서**(§5 템플릿) — Mode 2 결과 반영 후
6. [개발 모드] V750~ 버전맵 착수 / [개발자] Gold 확대 구매·작가 베타 탐색(GT-3)

## §10. 자기 점검 (논리적 약점)
- §4 Stage3 'necessity 씬 삭제 실험'은 다중에이전트 판정 의존 → GT-2 한계 내포. 완화: 일치율 보고+표본 확대.
- §5 버전맵 번호는 가정 — 개발 모드 실측으로 조정될 것을 전제로 한 골격.
- §8 H 스케치는 의도적 비구체 — 이것이 약점이 아니라 장치임을 명시.
- 본 문서는 docx 미작성(md 단일) — 개발자 열람용 docx 필요 시 후속 변환.

**문서 ID**: LOS-P1P5-REINFORCE-AXC-V1.0-2026-06-10 · 다음 정본 진입: INDEX → MASTER → 본 문서
