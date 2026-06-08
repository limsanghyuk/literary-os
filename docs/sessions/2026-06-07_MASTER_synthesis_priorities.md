# 전체 기획 종합 분석 + 우선순위 (MASTER, 2026-06-07)
개발자용 종합 설명서. 이번 세션 전체 산출물·검증결과·우선순위를 한 문서로. (정본 진입: INDEX → 본 문서 → 핸드오프 v3)

═══════════════════════════════════════════
## 1. 산출물 인벤토리 (이번 세션, 분류별)
═══════════════════════════════════════════
**A. 기획·로드맵 (Phase E~G·검증우선·UI)**
- phase_efg_planning(report+handoff): E~G 통합 로드맵(LLM-0→2.5)
- pre_phaseE_agenda_map: 6대 의제 맵
- phaseE_validation_first(proposal+blueprint+handoff) + v1.1_ensemble: 검증 우선 입구관문, 앙상블 에피소드 과제
- phaseE_ui_writer_claudedesign: 3-zone UI·작가개입·Claude Design
- home_continuation_playbook: 집 이어작업

**B. 아키텍처**
- agentic_orchestration_consensus(3인 합의): 엔진=도메인특화 에이전트 오케스트레이션, 공식=영속 검증 타입시스템

**C. 코어 알고리즘 6 (의사코드)**
- generation_orchestration(G7, 7패스) · nkg_load_consistency(G4) · critic_5axis(G5) · rag_context_builder(G9) · learning_loop(G6) · narrative_analyzer(G2)

**D. 데이터 (모델·구축·소싱·아키텍처)**
- data_model_v2(L0~L4 계층) · data_construction · data_architecture_upgrade(트라이스토어) · data_sourcing_method(A/B) · corpus_pipeline · data_adequacy(L0 부족 진단) · gold_candidate_availability(Gold20) · pathB_legal_script · tristore_poc

**E. 공식 검증 (실측)**
- formula_validation_roadmap(~25공식 인벤토리+Stage0~6) · formula_realdata_run · stage1-2_results · followup_results · reweight_heldout_CV · tristore_harness_integration · pilot_L2_DRSE

**F. 무결성·세션기록**
- SP-E0_integrity_remediation(진입 선결) · status_priorities_gaps · MVE_results · home_handoff_v2/v3

**코드·데이터**: tools/{formula_validation/[harness·heldout_cv·integrate_tristore]·tri_store/build_tristore·corpus_migrate} / data/corpus_seed/(L0 178편·POC·검증 씬셋)

═══════════════════════════════════════════
## 2. 핵심 분석 — 무엇을 만들고 무엇을 발견했나
═══════════════════════════════════════════
**만든 것(설계)**: Phase E~G 로드맵 + 아키텍처 정본 + 코어 알고리즘 6 골격 + 계층 데이터모델 + 트라이스토어 + 공식 검증 로드맵. 설계는 거의 완비.

**발견(실측·정직)**:
1. V745 무결성 결함: SHA256SUMS 자기검증 불가(매니페스트 미재생성) → 진입 선결 SP-E.0.
2. PROXY-MVE: 단일씬 구조프록시 vs 순수 LLM = 무승부+길이교란. → 얕은 프록시는 무의미, 깊은 파이프라인+앙상블 과제로 가야.
3. 공식 ~25개 전수조사: 거의 전부 실데이터 타당성 미검증, 일부 합성 더미로 동작.
4. 공식 실행·검증(하니스):
   - fitness 공식: held-out 교차검증 0.70 일반화(공식 미파손). 단 '재가중 0.40→0.59' 주장은 과적합으로 철회(held-out 효과 +0.002).
   - DRSE: TFIDF 0.02(복선 미탐지) → 임베딩 0.71(탐지). 임베딩 전환 필요 확정.
5. 데이터: L0 178편(작품요약)은 공식(씬단위 정량)·NKG·DRSE에 부족 → 트라이스토어(벡터+그래프+피처)로 보강, 5편 시범+하니스 연결 동작.
6. 듀얼 트랙: Claude(Literary/Sovereign OS V745)·GPT(V1700) 분리.

**메타 교훈**: ① 코드 인프라가 기획 가정보다 항상 더 풍부(NKG·Critic·RAG·학습 부품 다수 존재) → 설계는 '신설'이 아닌 '배선+빈칸'. ② 숫자가 좋아 보여도 교차검증 필수(과적합 자가 적발).

═══════════════════════════════════════════
## 3. 검증 결과 종합 (한눈에)
═══════════════════════════════════════════
| 실험 | 결과 | 상태 |
|---|---|---|
| V745 무결성 | 해시불일치 다수 | ⚠️ SP-E.0 선결 |
| PROXY-MVE(단일씬) | 무승부 | 프록시 무의미 |
| 공식 인벤토리 | ~25개 미검증 | 🔴 핵심 리스크 |
| fitness held-out | 0.70 일반화 | 공식 미파손(프록시) |
| DRSE 임베딩 | 0.71 vs TFIDF 0.02 | 임베딩 전환 확정 |
| 트라이스토어+하니스 | 연결 동작 | 인프라 가동 |

═══════════════════════════════════════════
## 4. 우선순위 (재산정 + 근거)
═══════════════════════════════════════════
| 순위 | 항목 | 근거 | 주체 |
|---|---|---|---|
| **P1** | SP-E.0 무결성 실행 | 진입 선결·비협상 | 개발(저연산) |
| **P2** | **데이터 깊이(Gold)+인간 GT** | **최대 병목**: 모든 공식 절대 타당성이 여기서 막힘. 경로B 대본집 4편+경로A 폭, 작가 베타 GT | 개발자 액션 |
| P3 | 공식 검증 Stage3~6 + DRSE BGE-M3 | 데이터 확보 시 ~25공식 타당성 측정 | 본 모드+개발 |
| P4 | 코어 모듈 구현(critic/·orchestration/) | 검증 통과 후 본격 빌드 | 개발 |
| P5 | UI/작가개입/Claude Design | 작가 사용·GT 수집 | 개발 |
| P6 | 결정 D1~D32·자금·사업 트랙 | 운영 | 개발자 |

**핵심 한 줄**: 설계는 충분하다. **지금 막힌 곳은 단 하나 — 데이터(Gold 깊이 + 인간 GT)**다. 공식이 진짜 타당한지는 여기서만 가려진다.

═══════════════════════════════════════════
## 5. 정직한 현재 위치 + 리스크
═══════════════════════════════════════════
- 설계: 거의 완비(로드맵·아키텍처·코어 알고리즘·데이터·검증 인프라).
- 검증: 메커니즘·프록시 단계 입증(공식이 돌고 실데이터를 먹음, 하니스가 과적합 적발). **절대 타당성은 미검증.**
- 최대 리스크: ① 데이터 병목(인간 GT·규모 없으면 공식 타당성 영원히 프록시). ② ~25공식 미검증 부채. ③ 1인 개발·자금.

═══════════════════════════════════════════
## 6. 개발자가 지금 할 것 (구체)
═══════════════════════════════════════════
1. **대본집 4편 입수**(비밀의숲·미생·우영우·우리들의블루스, 교보·알라딘) → 경로B Gold 깊이 시작.
2. **SP-E.0 무결성 실행**(generate_sha256sums.py + release_gate 게이트, 핸드오프대로).
3. **작가 베타 1~2명 섭외**(인간 GT — 공식 타당성의 유일한 절대 기준).
4. 확보되면 → 본 모드가 공식 검증 Stage 확대 + DRSE BGE-M3 전환.

> 협업 원칙: 누적·정리·발전. 본 문서가 현 시점 단일 종합. 다음 세션은 INDEX→본 문서→핸드오프 v3.
