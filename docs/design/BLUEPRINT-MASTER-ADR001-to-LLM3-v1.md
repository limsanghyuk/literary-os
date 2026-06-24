# BLUEPRINT-MASTER-ADR001-to-LLM3-v1 — 통합 청사진 1장 (ADR-001~249 + Phase A~천장 롤업)

- 상태: 통합 인덱스(PROPOSAL) · 2026-06-24 · 기준 허브 main `a71568c` / v14.0.0
- 목적: 그동안 분산돼 있던 청사진(REANCHOR·LLM-LADDER·Phase별 blueprint docx·ADR INDEX)을 **한 장으로 롤업**. "ADR-001부터 지금까지 무엇을 개발했는가"의 단일 답.
- 성격: 결정 문서 아님. 기존 정본들을 묶는 지도(SSOT 포인터).
- 연계 정본: DESIGN-ROADMAP-REANCHOR-v1(좌표), DESIGN-LLM-LADDER-v1(사다리 계약), docs/adr/INDEX.md(자동추출·stale), 각 Phase blueprint docx

---

## 0. 왜 이 문서 (발견된 결함)

조사 결과 통합 청사진 "한 장"은 **없었다**:
- `docs/adr/INDEX.md`는 자동추출이나 **ADR-041에서 멈춤**(현재 249까지 = 208개 누락 반영).
- ADR 문서 파일은 233개(**ADR-014~249**). **ADR-001~013은 문서 부재**(초기 암묵 결정, 소스 참조만).
- Phase별 청사진은 `docs/sessions/*blueprint*.docx`로 흩어짐(A/B/C/D 각각 별 파일).
- REANCHOR가 좌표를, LLM-LADDER가 사다리를 잡지만 **ADR 전체와 Phase를 한 표로 엮은 롤업은 부재**.

본 문서가 그 단일 롤업을 만든다.

---

## 1. 대축 — Phase ↔ 자율성 사다리 ↔ 버전 ↔ ADR ↔ 상태

| Phase | LLM 레벨 | 버전대 | 핵심 개발물 | ADR 군집(대략) | 상태 |
|---|---|---|---|---|---|
| **A** | LLM-0 결정론 코어 | ~V595 | 씬필요성·물리보상·NIE/MAE·CIM·스토리닥터·LLM0 정적게이트·LOSDB·LOS헌법 | 014~055 | ✅ |
| **B** | (틀 통합) | V596~630 | 시스템 통합·MultiWork CIM v2·백엔드 헬스·Helm·SystemIntegrationTest | 056~097 | ✅ |
| **C** | (자기학습) | V631~680 | 멀티에이전트 앙상블·자기학습·SDK·Sudowrite 흡수·정적타입게이트 | 098~142 | ✅ |
| **D** | (운영·신뢰) | V681~745 | 플러그인·Zero-Trust·통합테스트·Chaos 복원력·운영게이트 | 143~200 | ✅(잔여 7게이트 WIP) |
| **E** | **LLM-1 쌍대 Critic** | V746~795 | Critic 5축·loop-C·GPU 3모드·생성본체 7-pass·자체평가 M1/M2/M3·P0 페어링·**졸업** | 201~249 | **✅ v14.0.0 졸업(2026-06-24)** |
| **F** | LLM-1.5 | V796~875 | 판정 8B→프론티어 격상·공식 플로어 후퇴·코퍼스200·다언어 | 250~ (예정) | ◻ 기획 누적 중 |
| **G** | LLM-2~2.5 생성주력 | V876~955 | LLM 생성 주력·자율 평가루프·B2B SaaS | — | ◻ 기획 누적 중 |
| **천장** | LLM-3 | V956~ | 블라인드 인간평가 비열위(모작 상한) | — | ◻ 개념 |

> ADR 군집 경계는 근사(ADR 번호와 V버전이 1:1 아님). 정밀 매핑은 각 ADR 헤더의 V태그 참조.

---

## 2. Phase E 내부 — SP-E.x 상세 (현재 위치 확대)

가장 최근이자 졸업이 일어난 Phase. REANCHOR §3 정본 복제.

| SP | 버전 | 내용 | 게이트 | 상태 |
|---|---|---|---|---|
| SP-E.0 | V746~752 | 검증주간·corpus 무결성·인간GT·NER | G_INTEGRITY_MANIFEST | ✅ |
| SP-E.2 | V753~761 | LLM-1 Critic 5축·ensemble·alignment·arbitration | G_LLM1_* | ✅ |
| SP-E.4 | V762~766 | RLAIF loop-C 코어 + 전이 Exit | PHASE-E-LLM1-EXIT | ✅ |
| SP-E.5 | V767~780 | GPU 3모드·클라우드 실연동·분업·loop-C 폐회로 | G_LOOPC_WINRATE·G_GPU_ROUTING | ✅ |
| SP-E.6 | V781~787 | 생성본체 7-pass L4·자체평가 M1/M2/M3·클라우드 저장노드 | G_E2E_PROSE | ✅ |
| SP-E.7 | V788~792 | 측정정합: per-token·c3·KL0.50·암기게이트 E4·P0 페어링(I1~I5) | G_STRUCTURE·I1~I5·E4 | ✅ |
| SP-E.8 | V793 | 데이터 스케일: 한국드라마03 편입(2,030→2,339)·임베딩 전수 | (데이터 무결성) | ✅ |
| SP-E.9 | V794 | per-token loop-C 졸업급 측정(혼합 5/5 ADOPT) | G_LOOPC_WINRATE(per-token) | ✅ |
| **SP-E.10** | V795 | **Phase E Exit — 통합 누적 루프 → LLM-1→2 졸업 확정(v14.0.0)** | PHASE-E-EXIT | **✅ 졸업(ADR-249)** |

**졸업 증거**: `round_records_v3.json` 5/5 adopt, per-token W 0.580→0.808 단조상승, 전라운드 CI하한>0.5·lrr=0·c3 PASS, graduation_invariant 6/6. (상세=ADR-249 / memory project_pathB_hardsignal_generator)

---

## 3. ADR 군집 주제 지도 (대표 ADR로 본 개발 궤적)

번호 범위별 "그때 무엇을 지었나"를 대표 ADR 제목으로 요약(실파일 확인).

| 범위 | 대표 ADR | 주제 |
|---|---|---|
| 014~031 | 014 씬필요성 · 015 물리보상브릿지 · 018 CIM · 031 LLM0 정적게이트 | LLM-0 결정론 기관 정초 |
| 032~048 | 032 ADR 자동화 · 043~045 LOSDB 어댑터 | 자동화·DB Phase A |
| 050~070 | 050 백엔드헬스 · 070 MultiWork CIM v2 | 시스템 통합(B) |
| 090~110 | 090 SystemIntegrationTest+Helm · 110 AgentCoordinator(멀티에이전트) | 통합테스트·멀티에이전트(B/C) |
| 130~150 | 130 Sudowrite 흡수 · 150 정적타입게이트(G82) | 경쟁 흡수·타입안전(C) |
| 170~190 | 170 SP-D.2 통합테스트 · 190 Chaos 복원력(G89) | 운영 신뢰성(D) |
| 210~230 | 210 validation 생애주기 · 230 ParetoRouter(GPU 라우팅) | 공식 상설화·GPU(D/E) |
| 240~249 | 245 자체평가 M3 · 247 클라우드 학습노드 · **249 졸업** | 자체평가·졸업(E) |

---

## 4. 누적 통계 (실측 스냅샷)

| 지표 | 값 | 출처 |
|---|---|---|
| ADR 문서 | 233개(014~249) | `ls docs/adr` |
| 테스트 케이스 | ~11,497 (V794) | memory project_v794 |
| 게이트 | 90/97 통과(잔여 7=Phase D WIP) | memory |
| 코퍼스 | 2,339작품·239,768 ChromaDB·features 전수 | SP-E.8 |
| 졸업 버전 | v14.0.0 (Phase E Exit) | ADR-249 |
| 코어 생성기관 | 16개(15 LLM 0회 = 결정론 골격) | DESIGN-LLM2-BLANK-SLOTS-v1 §2 |

---

## 5. 빈칸·전방 의제 (한눈에)

| 의제 | 정본 문서 | 상태 |
|---|---|---|
| Synopsis Assembler(자율 머리) | SYNOPSIS-ASSEMBLER-v1 / IO-MERGE-v1 | 설계 수렴, 미구현 |
| 빈칸 5종(세계관·주제·인물창작·track_axis·causal_spine) | **BLANK-SLOTS-v1** | 확정, 미구현 |
| 넓은 실측(거시·다축·메타게이트) | **BROAD-MEASUREMENT-v1** | 설계, 무GPU 1~3단계 착수가능 |
| 판단 이양(8B→프론티어) | PHASE-F-LLM15-v1, INDEX O9 | 기획 누적 |
| 8B 역할분담(get_episode_brief) | CAPACITY-DIVISION-v1 | 설계 |

---

## 6. 결과·다음

- **산출**: 분산 청사진을 단일 롤업 1장으로 통합(Phase A~천장 × LLM레벨 × 버전 × ADR군집 × 상태 + SP-E.x 상세 + ADR 궤적 지도 + 누적 통계 + 전방 의제).
- **해소한 결함**: "통합 청사진 부재" + "ADR INDEX 041에서 stale".
- **권고**: ① `docs/adr/INDEX.md` 자동추출기(`tools/extract_adr.py`)를 249까지 재실행해 stale 해소 ② 본 문서를 README의 "전체 지도" 링크로 등재.

### 자기점검 (논리적 약점)
1. **ADR↔Phase 경계 근사**: 번호 군집은 V태그 기반 추정. 정밀 1:1은 각 ADR 헤더 확인 필요 — 본 표는 "대략"임을 명시.
2. **ADR-001~013 내용 미복원**: 문서 부재라 소스 참조 수(각 4~7건)만 알 뿐 실내용은 코드 고고학 필요(별도 작업).
3. **통계 스냅샷 시점**: TC·게이트 수는 V794 기준. 졸업 후 v14.0.0에서 변동 가능(미재측정).
4. 본 문서는 **포인터 인덱스**지 정본 대체 아님 — 각 셀의 권위는 연계 정본에 있다.
