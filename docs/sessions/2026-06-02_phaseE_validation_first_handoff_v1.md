# Phase E 검증 우선 — 제안서+설계도 핸드오프

**작성일**: 2026-06-02
**기준선**: V745 (v13.0.0) / 선행 E~G 통합기획 v1.0 (HEAD 5536758)
**문서**:
- `docs/sessions/2026-06-02_phaseE_validation_first_proposal_v1.docx`
- `docs/sessions/2026-06-02_phaseE_validation_first_blueprint_v1.docx`
- `docs/sessions/2026-06-02_phaseE_validation_first_handoff_v1.md`

## 1. 핵심 결정
Phase E 최우선 = **구조+LLM vs 순수 LLM 적합성 검증**. 이 가설이 참이어야 F·G·자금이 의미.
- 변경점 2개(기존 v1.0 버전맵 유지): ① 종료 게이트를 **G_VALUE_PROOF**(블라인드 작가 선호 실험)로 격상, ② **MVE**(소표본 최소실현실험) V774~775 삽입.
- 앞단(코퍼스·LLM-1)은 실험 가능 최소치까지만 우선.

## 2. 공식 관점 재정의 (개발자 지적 반영)
공식 = 학습 가능한 **해석적 prior/Critic**(대체 아님, AI 약점 교정 가드레일). 계수는 gradient로 학습·보정.
- 근거(V745 실측): `learning/physics_coefficient_updater.py`(gd, lr 0.01), `optimizer/update_coordinator.py`(공식↔학습 store 동기 게이트) 이미 존재.
- ML 주류(reward/critic/RLAIF/verifier)와 정합.

## 3. 두 겹 검증
- 검증1: 구조+LLM > 순수 LLM (작가 블라인드 선호, 사전등록 임계 B≥60%, p<0.05).
- 검증2: 해석적 공식-Critic ≈/> 블랙박스 보상모델 (품질 동등 + 감사가능성·통제성 우위). 실패 시 공식 가치는 감사가능성 프리미엄으로 축소.

## 4. 실험 설계 요지
arm A(순수 LLM) / B(구조+LLM, 동일 LLM·온도·토큰예산) / C(상용, 옵션). 동일 프롬프트, 블라인드·순서 무작위. MVE 10~15씬·작가 2~3, 본실험 40~60씬·작가 5+. 사전등록(preregister.json) 후 분석.

## 5. 공식 진화 명세 (LearnableCritic)
CriticInterface 하위 LearnableCritic. 루프: evaluate→err=target−score→updater.update_one_epoch(lr0.01)→coordinator.tick_and_sync→alignment_monitor.record. 일치율 낮은 축 계수 재학습 우선. 보상모델 ablation 포함.

## 6. 결정 요청 D16~D20
D16 검증우선 채택 / D17 MVE V774~775 / D18 사전등록 임계 / D19 작가 5+ 모집 / D20 공식진화+ablation 범위.

## 7. 전제·보안
LLM API 자격증명은 환경변수 전용·마스킹·커밋/채팅 노출 0으로 실행 단계에서만 사용. Gold 30편 선인덱싱, LLM-1 생성 1팔 최소연결(V773) 선행.

## 8. 다음
저연산 모드: experiments/value_proof/ harness·blind_eval·metrics·ablation·preregister 구현 → MVE 실행 → 게이트 판정.
