# DESIGN-ROADMAP-REANCHOR-v1 — Phase 단계 재정렬 + LLM-1 졸업 지도

- 상태: 제안(PROPOSAL) · 2026-06-21 · 기준 HEAD 720141d (v13.45.1 / V793)
- 목적: **"지금 어느 Phase의 어느 단계인가"가 V767 이후 불명확**해진 문제를 해소. V767~793을 Phase E 하위로 재정렬하고 LLM-1 졸업까지 게이트 지도를 못 박는다.
- 감독: SPE · 연계: DESIGN-LLM-LADDER-v1, DESIGN-DATA-EVAL-DELIBERATION-v1, DESIGN-P0-PAIRING-BUILDER-v1, project Phase E v1.0

---

## 0. 문제 제기 (왜 이 문서)
Phase A~D, Phase E.2(V753~761)·E.4(V762~766)까지는 **SP-x.x 단위**라 "지금 어느 칸"이 명확했다.
그러나 **V767부터(E.4확장·생성본체·자체평가·SGATE·LADDER·DELIBERATION·MEMGATE·P0·데이터스케일)는 명명 트랙(named track)으로 흩어져 SP-E.x 라벨이 끊겼다.** 버전(V767→V793)은 올랐으나 Phase 좌표가 사라졌다. 본 문서가 그 좌표를 복원한다.

## 1. 현재 위치 (한 줄)
**Phase E (LLM-1) · v13.45.1 / V793. E.4 전이 Exit 통과 후, "LLM-1 졸업 선결조건" 트랙 거의 완료. 유일한 미실행 관문 = P3 실 GPU per-token dW 1라운드(RunPod 키만 차단).**

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
| **SP-E.8** | V793 | 데이터 스케일: 한국드라마03 편입(2,030→2,339)·임베딩 전수 | (데이터 무결성) | ◀ 진행(임베딩 완료, 집 ChromaDB/features 잔여) |
| **SP-E.9** | V794~ | **★P3 실 GPU per-token dW 1라운드 → LLM-1 졸업 게이트 실측** | **G_LOOPC_WINRATE(per-token)** | ⛔ **차단(RunPod 키)** |
| **SP-E.10** | V795 | Phase E Exit — LLM-1→2 졸업 확정(v14.0.0) | PHASE-E-EXIT | ◻ |

> V767~793이 "어디였는지"가 이제 SP-E.5~E.8로 복원됨. 현재 칸 = **SP-E.8 마무리 / SP-E.9 진입 직전**.

## 4. 현재 관문 상세 — SP-E.9 = P3 졸업 라운드
- **선결(완료)**: P0 페어링 빌더(길이매칭·per-token·E4 암기·작품분리), 구조게이트 c3, 데이터 2,339편+임베딩 24만 청크.
- **실행(미完)**: 실 GPU에서 P0 산출 선호쌍으로 DPO 1라운드 → `G_LOOPC_WINRATE = c1(per-token dW>0) ∧ c2(KL≤0.50) ∧ c3(구조 비퇴행)` 실측.
- **왜 차단**: Round#2 교훈(sum-logp dW는 길이 인공물, per-token dW=0)으로 **단발이 아니라 신뢰 라운드가 필요**. 집 4070(12GB)은 단발 측정엔 가능하나 졸업(누적 adopt)엔 클라우드 권장 → **RunPod GPU 키가 유일 차단점**(미제공).

## 5. Phase E Exit (v14.0.0) 졸업 계약 (LLM-1→2)
DESIGN-LLM-LADDER §3.3 준수: **adopt≥5연속(롤백0) · Σn_pairs≥250 · per-token W₁ 95%CI 하한>0.5 · 길이단순규칙 재현율≤0.60 · 전라운드 c3 PASS · 비용 게이트 녹색.** sumlogP 원점수 금지(ADR-LADDER-3).

## 6. 이후 로드맵 (F·G·천장)
- **Phase F (LLM-1.5, V796~875)**: 5축 전체 AI 전환 + 생성 초안에 한해 공식 완화. 코퍼스 200편·다언어 확장. 진입=5축 동시 자격통과 ∧ 비용 게이트.
- **Phase G (LLM-2~2.5, V876~955)**: LLM 생성 주력(공식=안전 바닥만) → 자율 평가루프 → B2B SaaS. 진입=신뢰 라운드 누적 ∧ 자가평가 κ≥0.6.
- **천장 LLM-3 (V956~)**: 블라인드 인간평가에서 생성 신작이 실명작 대비 비열위(95%CI 하한≥0.45). 정직 한계=모작 수준, 인간 GT=최종시험.

## 7. 즉시 액션 (개발자 합의 요청)
1. **README SSOT에 SP-E.5~E.10 라벨 복원**(본 §3 반영) → "지금 어느 칸" 상시 가시화.
2. **SP-E.9(P3 라운드)를 Phase E의 단일 차단 관문으로 공식화** → RunPod 키 확보를 최우선 의제로.
3. P2.5 구조추출패스·Phase D 잔여 7게이트는 **병렬 보조 트랙**(졸업 비차단).
4. 데이터: SP-E.8 잔여(집 ChromaDB/features 풀런)는 집 1회 작업으로 종결.

## 8. 자기점검 (논리적 약점)
1. **Phase E가 계획(V746~795)보다 길어짐**: 이미 V793인데 졸업 미完. 졸업이 실 GPU에 막혀 범위 초과 → Phase E를 V795→V800±로 연장하거나 졸업 정의를 단발+누적 2단계로 분리하는 결정 필요(개발자 판단).
2. **졸업 임계 미실측**: 5라운드·CI하한 0.5·재현율 0.60은 P3 1라운드 후 캘리브레이션 전까지 잠정.
3. **집 4070 vs 클라우드**: 4070 단발로 SP-E.9 *부분*(1라운드 per-token dW) 실측은 가능 → RunPod 없이도 "졸업 게이트 첫 실측"까지는 전진 가능, 누적 5라운드만 클라우드 대기.
