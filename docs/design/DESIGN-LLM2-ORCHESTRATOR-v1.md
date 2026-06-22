# DESIGN-LLM2-ORCHESTRATOR-v1 — LLM-2 생성 주력 본체 (미설계 핵심 빈칸 채움)

상태: 제안 · 2026-06-21 · LADDER §4 빈칸("L2 생성 주력 오케스트레이터") + DELIBERATION "DESIGN-HIER-PLANNER 미착수" 충족.
정합: DESIGN-LLM-LADDER-v1(§3.3 진입계약)·DESIGN-GRADUATION-V2(졸업)·ADR-241(7-pass)·ADR-243(천장=모작).

## 0. 위치
LLM-1(쌍대 Critic+per-token loop-C)은 **미시 씬 craft**를 안전하게 학습(실증 완료). LLM-2 = **LLM이 생성을 주도**하고 공식은 안전 바닥만 감시하는 단계. 그러나 *16부작(1,000+씬)을 하나로 엮는 거시 설계*가 미설계 빈칸이었다. 본 문서가 그 본체를 설계한다.

## 1. 문제 재확인 (unit-of-learning mismatch)
16부 × ~60씬 = 3층 동시 정합:
- **L4 거시**: 시즌 아크·복선→페이오프(1화→16화)·인물 장기궤적.
- **L3 회차**: 회차 구조·클리프행어·막전환.
- **L2 씬**: 씬 craft(보여주기·대사·긴장) ← LLM-1 loop-C가 담당(완료).
씬 단위 DPO는 L4/L3를 **원리적으로 학습 못 함**(DELIBERATION B2). → **계층 플래너 + 아크 구조게이트**가 L4/L3를 맡는다(DPO 밖 트랙).

## 2. ★핵심 통찰 — 본체는 이미 절반 있다
- **7-pass(V781, ADR-241)가 계층 골격**: Pass1 장르곡선 / Pass2 모티프·페이오프스케줄 / Pass3 slug·POV·knowledge_delta / Pass4 RAG / Pass5 생성기 / Pass6 LOSConstitution R / Pass7 쌍대→loop-C. = 거시→씬 파이프라인 초안.
- **고립 schema 11종이 LLM-2 데이터 계약**(GitNexus 감사서 적발): intent_seed/commander_briefing/pressure_cast_plan/residue_variation_plan/character_grid/scene_digest/critic_decision/format_constitution/final_acceptance/literary_state_snapshot/character_birth_gate. = *정의됐으나 미배선된 계층 패킷*. **LLM-2 = 이 패킷들을 7-pass에 배선해 계층 오케스트레이터로 승격하는 것.**
- **NKG**(2,351작품·139K노드)가 일관성 백본: 인물·복선·타임라인 상태 추적(Pass3/5 knowledge_state).

## 3. 아키텍처 (계층 생성)
```
intent_seed_packet(기획씨앗: 장르·길이·PDI)
  → [L4 플래너] story_bible(인물·세계·테마·복선맵) + season_arc(16부 곡선)   ← 공식: 아크 구조게이트
  → [L3 플래너] commander_briefing/회차 beat-sheet(클리프행어·막) ×16        ← 공식: 회차 긴장곡선
  → [L2 생성]  scene_digest→scene_brief→씬 생성(LLM-1 craft)×~60/회         ← 공식: 분포가드·암기게이트·c3
  → literary_state_snapshot(NKG 상태 갱신: 복선 심음/회수 추적)
  → final_acceptance_packet(전편 통합 검수)
```
- **LLM 권한**: 각 층 생성 + 자기수정 제안.
- **공식 권한 = 안전 바닥만**(LADDER 불변식): 사전강제 최소, 사후 비퇴행 검열(ΔW·KL·c3·암기·분포).

## 4. 거시 구조게이트 (c3 확장)
현 c3(R_struct/R_pair/R_path)는 씬 단위. **아크 단위로 확장**:
- **plant→payoff 회차경계**: 1화 심은 모티프가 N화에 회수되는지(NKG payoff_scheduler, 전역).
- **인물 궤적 일관성**: knowledge_state_tracker로 회차간 인물 상태 모순 검출.
- **시즌 긴장 곡선**: 16부 긴장 프록시가 목표 아크밴드 내(드라마투르기).

## 5. 학습 vs 규칙 (크레딧 할당)
- **미시(씬)**: loop-C DPO(완료). 
- **거시(아크)**: DPO 밖 → 계층 플래너는 (a)규칙/검색(코퍼스 아크 패턴 DRSE) + (b)구조게이트 사후검열. 장문(long-context) 페어 학습은 미검증 후속(ARCH §8).
- **크레딧 할당 계약**(빈칸): 전편 평가가 갈렸을 때 어느 층(아크/회차/씬)·어느 축 기여인지 인터페이스 필요 → UniformCreditAssigner(P4 스텁) 확장.

## 6. 진입(졸업)·천장
- LLM-1→2 진입: §3.3 + GRADUATION-V2(마스터-후-유지, per-round KL).
- **천장(정직)**: 모작(pastiche). 전편 생성이 가능해도 *인간 명작 대체가 아니라 강력한 공동작가/초안엔진*. 인간 GT=최종시험(ADR-243).

## 7. 로드맵 (Phase G, V876~)
1. schema 11종 배선 → 7-pass를 계층 오케스트레이터로 (intent_seed→story_bible→arc→beat→scene).
2. 거시 c3(아크 plant→payoff·인물궤적·긴장곡선) 구현.
3. 1회차 전편(60씬) E2E 생성 PoC → 구조게이트.
4. 16부 전편 통합 + final_acceptance.
5. LLM-2.5(자가평가 폐루프, κ게이트) → B2B SaaS.

## 8. 자기점검
- 거시 학습 방식(규칙 vs 장문DPO) 미실측 — PoC 후 결정.
- 크레딧 할당·아크 c3 임계 미실측(휴리스틱).
- 천장 한계 정직 유지: 본 설계는 "전편 초안 생성 가능"이 목표지 "명작 자율창작"이 아님.
