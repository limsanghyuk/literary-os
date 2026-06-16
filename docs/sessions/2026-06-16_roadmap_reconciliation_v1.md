# 로드맵 정합화 보고서 v1 — 기존 Phase E 기획 ↔ 실제 진행 (V746~V768)

작성: 2026-06-16 (기준 v13.19.0, V766 완료) · 작성자: CSA×CSC×CSPE 3인 합의

## 0. 목적

기존 **Phase E 본안 v1.0**(2026-05-30, V745 기준, 6 SP / V746~V820 / v14.0.0)의 계획 순서와,
실제 진행된 V746~V766 + 신규 삽입 V767~V768(GPU 학습 3-모드)을 대조하여
**분기점을 식별·정정하고 정합화된 단일 로드맵**으로 허브에 고정한다.

---

## 1. 계획(Plan) — Phase E 본안 v1.0

| SP | 버전 | 핵심 | 계획 ADR | 계획 release |
|---|---|---|---|---|
| E.1 | V746~V760 | 코퍼스 50편 + Gold 30 + ChromaDB | 211~215 | v13.1.0 |
| E.2 | V761~V775 | AI Critic + LLM-1 부분완화 | 216~220 | v13.2.0 |
| E.3 | V776~V790 | 작가 UI MVP | 221~225 | v13.3.0 |
| E.4 | V791~V800 | RLAIF (DPO+best-of-n+KL) | 226~230 | v13.4.0 |
| E.5 | V801~V810 | KEDA 실배포 + Java SDK | 231~235 | v13.5.0 |
| E.6 | V811~V820 | Phase E Exit G110 8축 + Phase F 트레이스 | 236~240 | v14.0.0 |

게이트 계획: G96~G110(번호). 총 +1,500 TC.

## 2. 실제(Actual) — V746~V766

| 버전 | 내용 | ADR | release | 트랙 |
|---|---|---|---|---|
| V746 | WP-0 G_INTEGRITY_MANIFEST | 209 | 13.0.1 | 검증주간 |
| V747 | WP-1 validation 생애주기 | 210 | 13.1.0 | 검증주간 |
| V748 | WP-4b Pairwise 패러다임 | 211 | 13.2.0 | 검증주간 |
| V749 | G_PAIRWISE_REGRESSION+G_TRANSITIVITY | 212 | 13.3.0 | 검증주간 |
| V750 | G_HUMAN_GT_ALIGNMENT(인간 GT) | 213 | 13.4.0 | E.0 기반 |
| V751 | char_ner 시리즈 NER | — | 13.5.0 | E.0 기반 |
| V752 | 생성 본체 Pass4~7 | — | 13.6.0 | E.0 기반 |
| V753~V761 | LLM-1 Critic(critic/ 8모듈+SP-E.2 Exit) | 214~221 | 13.7~13.14 | **E.2** |
| V762~V765 | RLAIF loop-C·보상·오케·트리거 | 222~225 | 13.15~13.18 | **E.4** |
| V766 | LLM-1 전이 트랙 Exit 게이트 | 226 | 13.19.0 | 전이 Exit |

게이트 실제: **named 게이트**(G_INTEGRITY_MANIFEST, G_HUMAN_GT_ALIGNMENT, G_LLM1_BOUNDARY/RAG/ALIGNMENT/SAFETY/COST, PHASE-E-LLM1-EXIT). G96~G110 번호 미사용.

---

## 3. 분기점 8건 (Plan ↔ Actual)

| # | 분기 | 원인 | 판정 |
|---|---|---|---|
| D1 | **앞단 검증주간 삽입**(V746~V749, WP-0~4b) | V745 직후 무결성·pairwise 검증 인프라 선행 필요 | ✅ 정당(전체 4칸 밀림 수용) |
| D2 | **SP-E.1 코퍼스가 버전 트랙 밖** | 개발자가 코퍼스 455편을 로컬 별도 구축 | ✅ 정당(트랙 외 자산, human_gt/Pass4-7이 소비) |
| D3 | **E.3(UI) ↔ E.4(RLAIF) 순서 역전** | 2단계 제품 비전: 자율생성 먼저, 협업/UI 후순위 | ✅ 의도된 재배열(사용자 확인) |
| D4 | **ADR 번호 4칸 앞당김** | 계획 211~240이 실제 209~226으로 시작·압축 | ⚠️ 재매핑 필요(§4) |
| D5 | **"E.5" 명칭 충돌** | V766 "E.5 전이 Exit" vs 계획 "SP-E.5 KEDA" | ⚠️ 정정: V766="LLM-1 전이 트랙 Exit"(공식 SP-E.5 아님) |
| D6 | **게이트 번호 체계 분기** | named 게이트 채택, G96~G110 미사용 | ⚠️ named 체계 공식화(§5) |
| D7 | **릴리스 케이던스 분기** | 계획 SP당 minor 1 → 실제 버전당 minor 1 | ✅ 버전당 minor 공식 채택 |
| D8 | **신규 V767~V768 GPU 3-모드 삽입** | RTX 4070 발견 → 로컬/클라우드/하이브리드 학습 | ✅ SP-E.4(RLAIF) 확장으로 편입 |

---

## 4. ADR 재매핑 (실제 기준 고정)

계획의 ADR 211~240 할당은 **outdated**. 실제 확정 매핑:

| ADR | 버전 | 주제 |
|---|---|---|
| 209~213 | V746~V750 | 검증주간 5종(integrity/validation/pairwise/regression/human-GT) |
| 214~221 | V753~V761 | LLM-1 Critic 8종 |
| 222~225 | V762~V765 | RLAIF 4종(loop-C/보상/오케/트리거) |
| 226 | V766 | LLM-1 전이 트랙 Exit |
| **227** | **V767** | **LocalGPUAdapter(4070 QLoRA)** |
| **228** | **V768** | **ProviderRouter(3-모드 라우팅)** |

## 5. 게이트 체계 공식화

번호 게이트(G96~G110) → **named 게이트**로 공식 전환. Phase E 전이 트랙 게이트:
`G_INTEGRITY_MANIFEST`, `G_PAIRWISE_REGRESSION`, `G_TRANSITIVITY`, `G_HUMAN_GT_ALIGNMENT`,
`G_LLM1_BOUNDARY/RAG/ALIGNMENT/SAFETY/COST`, `PHASE-E-LLM1-EXIT`, (신규) `G_GPU_ROUTING`(V768).

---

## 6. 정합화된 단일 로드맵 (Reconciled)

### 6.1 완료 — Phase E "LLM-1 전이 트랙" (V746~V766) ✅
검증주간 → E.0 기반(GT/NER/Pass4-7) → E.2 LLM-1 Critic → E.4 RLAIF → 전이 Exit. v13.19.0.

### 6.2 진행 — E.4 확장: GPU 학습 3-모드 (V767~V768)
- V767 LocalGPUAdapter(4070 QLoRA, ADR-227) → V768 ProviderRouter(3-모드, ADR-228).
- 설계도: `docs/sessions/2026-06-16_gpu_3mode_blueprint_v1.docx`(3인 합의).

### 6.3 잔여 — 공식 Phase E 후반 (V769~V820)
계획 대비 **미이행 잔여**를 명시(폐기 아님, 후순위·재배치):

| 잔여 항목 | 계획 위치 | 정합화 위치 | 비고 |
|---|---|---|---|
| 작가 UI MVP | SP-E.3 | **Phase E 후반(2단계)** | 자율생성 성숙 후 |
| 분업 파이프라인(로컬↔클라우드) | 신규 | V769 PoC | GPU 3-모드 후속 |
| KEDA 실배포 + Java SDK | SP-E.5 | Phase E 후반/F 인접 | B2B 수익 연계 |
| 공식 Phase E Exit(8축) + v14.0.0 | SP-E.6 | Phase E 종료 시 | UI/KEDA 완료 후 |

### 6.4 불변 (3인 합의)
- LLM-0 경계: critic/만 LLM-1, corpus/constitution/finetune은 LLM-0 유지.
- RULE-0 Preflight 매 버전 강제. PACKAGING_PROTOCOL_v1.0. V665_R 위생(outputs 격리).
- 매 버전 완료 → 전체 통합 레포 ZIP 제공.

---

## 7. 결론

실제 진행은 계획에서 **8개 분기**가 있었으나 D1·D2·D3·D7·D8은 정당/의도된 것이고,
D4·D5·D6은 본 문서로 정정·재매핑하여 정합화한다. 핵심은 **(a) UI(SP-E.3)의 의도적 후순위,
(b) RLAIF 선행, (c) GPU 3-모드 신규 삽입(V767~V768), (d) named 게이트·버전당 minor 공식화**.
공식 Phase E의 잔여(UI/KEDA/SDK/공식 Exit/v14.0.0)는 폐기가 아니라 §6.3으로 재배치한다.
