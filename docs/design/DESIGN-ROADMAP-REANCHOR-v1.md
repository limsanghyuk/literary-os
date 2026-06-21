# DESIGN-ROADMAP-REANCHOR-v1 — Phase 단계 재정렬 + LLM-1 졸업 지도

- 상태: 제안(PROPOSAL) · 2026-06-21 · 기준 HEAD 720141d (v13.45.1 / V793)
- 목적: **"지금 어느 Phase의 어느 단계인가"가 V767 이후 불명확**해진 문제를 해소. V767~793을 Phase E 하위로 재정렬하고 LLM-1 졸업까지 게이트 지도를 못 박는다.
- 감독: SPE · 연계: DESIGN-LLM-LADDER-v1, DESIGN-DATA-EVAL-DELIBERATION-v1, DESIGN-P0-PAIRING-BUILDER-v1, project Phase E v1.0

---

> ⚠️ **[2026-06-21 SSOT 정정 — 본 문서 일부 SUPERSEDED]** 본 문서는 기준 HEAD 720141d 시점 스냅샷이다. 그 직후 집 RTX 4070(12GB) 단독으로 **per-token loop-C 혼합 5/5 ADOPT**가 실증되어 **SP-E.9는 완료**됐다(정본 = `docs/sessions/2026-06-21_MASTER_session_summary.md`). 따라서 아래의 "SP-E.9 ⛔차단(RunPod 키)" 서술은 **무효**다. 현재 칸 = **SP-E.9 완료 → SP-E.10(통합 누적 루프) 진입**. RunPod는 졸업 비차단(편의 옵션)으로 강등.

## 0. 문제 제기 (왜 이 문서)
Phase A~D, Phase E.2(V753~761)·E.4(V762~766)까지는 **SP-x.x 단위**라 "지금 어느 칸"이 명확했다.
그러나 **V767부터(E.4확장·생성본체·자체평가·SGATE·LADDER·DELIBERATION·MEMGATE·P0·데이터스케일)는 명명 트랙(named track)으로 흩어져 SP-E.x 라벨이 끊겼다.** 버전(V767→V793)은 올랐으나 Phase 좌표가 사라졌다. 본 문서가 그 좌표를 복원한다.

## 1. 현재 위치 (한 줄)
**Phase E (LLM-1) · v13.45.1 / V793. SP-E.9(per-token loop-C 졸업급 측정) 완료(4070 단독 5/5 ADOPT). 현재 칸 = SP-E.10 통합 누적 루프 진입. RunPod = 졸업 비차단(편의).**

## 2. 대축 정합 — Phase ↔ 자율성 사다리 ↔ 버전
| Phase | 사다리 | 버전대(계획) | 핵심 | 상태 |
|---|---|---|---|---|
| A | LLM-0 기반 | ~V595 | 결정론 코어(집, v10.0.2 고정) | ✅ |
| B | — | V596~630 | 시스템 통합 | ✅ |
| C | — | V631~680 | 자기학습·멀티에이전트·SDK | ✅ |
| D | — | V681~745 | 플러그인·Zero-Trust·운영 | ✅(잔여 7게이트 WIP) |
| **E** | **LLM-1 (쌍대 Critic)** | **V746~795** | **Critic 자격·loop-C·졸업 측정** | **◀ 현재 (V793)** |
| F | LLM-1.5 (5축 AI) | V796~875 | 5축 전체 AI + 생성초안 완화 + 코퍼스200·다언어 | ◻ |
| G | LLM-2~2.5 (생성주력) | V876~955 | 생성 주력 + 자율평가루프 + B2B SaaS | ◻ |
| 천장 | LLM-3 | V956~ | 블라인드 인간평가 비열위(모작 상한) | ◻ 개념 |

## 3. Phase E 내부 재정렬 (★SP-E.x 라벨 복원)
| SP | 버전 | 내용 | 게이트 | 상태 |
|---|---|---|---|---|
| SP-E.0 | V746~752 | 검증주간·corpus 무결성·인간GT 프로토콜·NER | G_INTEGRITY_MANIFEST | ✅ |
| SP-E.2 | V753~761 | LLM-1 Critic 5축·ensemble·alignment·arbitration | G_LLM1_BOUNDARY/RAG/ALIGNMENT/SAFETY/COST | ✅ |
| SP-E.4 | V762~766 | RLAIF loop-C 코어(보상·오케·트리거) + 전이 Exit | PHASE-E-LLM1-EXIT | ✅ |
| **SP-E.5** | V767~780 | GPU 3-모드·클라우드 실연동·분업·loop-C 폐회로·2축 품질라벨 | G_LOOPC_WINRATE·G_GPU_ROUTING | ✅ |
| **SP-E.6** | V781~787 | 생성본체 7-pass L4·자체평가 M1/M2/M3·클라우드 저장노드·M3 재보정 | G_E2E_PROSE·자체평가닻 | ✅ |
| **SP-E.7** | V788~792 | 측정정합: per-token 표준·구조게이트 c3·KL0.50·암기게이트 E4·P0 페어링 빌더(I1~I5) | G_STRUCTURE_CONFORMANCE·I1~I5·E4 | ✅ |
| **SP-E.8** | V793 | 데이터 스케일: 한국드라마03 편입(2,030→2,339)·임베딩 전수 | (데이터 무결성) | ✅ (임베딩 2,339·ChromaDB 239,768·features 충전 전수 완료, 2026-06-21) |
| **SP-E.9** | V794~ | **★per-token loop-C 졸업급 측정(혼합 5/5 ADOPT)** | **G_LOOPC_WINRATE(per-token)** | ✅ (4070 단독, 2026-06-21) |
| **SP-E.10** | V795 | Phase E Exit — 통합 누적 루프(어댑터 체이닝 5연속 adopt) → LLM-1→2 졸업 확정(v14.0.0) | PHASE-E-EXIT | ◀ 진입 |

> V767~793이 "어디였는지"가 SP-E.5~E.8로 복원됨. SP-E.8·E.9 완료(2026-06-21). 현재 칸 = **SP-E.10 진입(통합 누적 루프)**.

## 4. 현재 관문 상세 — SP-E.10 = 통합 누적 루프 (SP-E.9는 완료)
- **SP-E.9 완료(2026-06-21)**: 집 4070(12GB) QLoRA DPO로 per-token loop-C 실증 — Round#2 길이착시 ROLLBACK → P1 메커니즘 → P3 craft(+0.404) → c3 안전 → **혼합 P1+P3+P2 독립분할 5/5 ADOPT**(dW_pt +0.20~0.26, KL 0.06~0.08, CI하한~0.65>0.5). standalone 측정·게이트 증명 종료. A100/H100·RunPod 불요.
- **SP-E.10 실행(진입)**: `loopc_closure.run_round`가 라운드 r마다 (a)직전 어댑터 로드 (b)신규 P0쌍 DPO (c)held per-token dW+KL (d)c3 (e)adopt면 어댑터 승격·rollback면 폐기. **5연속 adopt → Phase E Exit(v14.0.0)**.
- **RunPod 위상 변경**: 졸업 단일 차단점 → **비차단 편의 옵션**(4070으로 누적 라운드 가능, 클라우드는 가속용).

## 5. Phase E Exit (v14.0.0) 졸업 계약 (LLM-1→2)
DESIGN-LLM-LADDER §3.3 준수: **adopt≥5연속(롤백0) · Σn_pairs≥250 · per-token W₁ 95%CI 하한>0.5 · 길이단순규칙 재현율≤0.60 · 전라운드 c3 PASS · 비용 게이트 녹색.** sumlogP 원점수 금지(ADR-LADDER-3).

## 6. 이후 로드맵 (F·G·천장)
- **Phase F (LLM-1.5, V796~875)**: 5축 전체 AI 전환 + 생성 초안에 한해 공식 완화. 코퍼스 200편·다언어 확장. 진입=5축 동시 자격통과 ∧ 비용 게이트.
- **Phase G (LLM-2~2.5, V876~955)**: LLM 생성 주력(공식=안전 바닥만) → 자율 평가루프 → B2B SaaS. 진입=신뢰 라운드 누적 ∧ 자가평가 κ≥0.6.
- **천장 LLM-3 (V956~)**: 블라인드 인간평가에서 생성 신작이 실명작 대비 비열위(95%CI 하한≥0.45). 정직 한계=모작 수준, 인간 GT=최종시험.

## 7. 즉시 액션 (개발자 합의 요청)
1. **README SSOT에 SP-E.5~E.10 라벨 복원**(본 §3 반영) → "지금 어느 칸" 상시 가시화.
2. ~~SP-E.9를 단일 차단 관문으로 공식화~~ → **[정정] SP-E.9 완료. 현 관문 = SP-E.10 통합 누적 루프(어댑터 체이닝 구현 + 5연속 adopt 실측).** RunPod는 비차단 편의.
3. P2.5 구조추출패스·Phase D 잔여 7게이트는 **병렬 보조 트랙**(졸업 비차단).
4. 데이터: SP-E.8 잔여(집 ChromaDB/features 풀런)는 집 1회 작업으로 종결.

## 8. 자기점검 (논리적 약점)
1. **Phase E가 계획(V746~795)보다 길어짐**: 이미 V793인데 졸업 미完. 졸업이 실 GPU에 막혀 범위 초과 → Phase E를 V795→V800±로 연장하거나 졸업 정의를 단발+누적 2단계로 분리하는 결정 필요(개발자 판단).
2. **졸업 임계 미실측**: 5라운드·CI하한 0.5·재현율 0.60은 P3 1라운드 후 캘리브레이션 전까지 잠정.
3. **집 4070 vs 클라우드**: 4070 단발로 SP-E.9 *부분*(1라운드 per-token dW) 실측은 가능 → RunPod 없이도 "졸업 게이트 첫 실측"까지는 전진 가능, 누적 5라운드만 클라우드 대기.
