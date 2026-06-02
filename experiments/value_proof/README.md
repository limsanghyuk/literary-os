# Phase E 가치검증 PROXY-MVE — 재현 패키지 (2026-06-02)

Claude(기획·설계 모드)가 실제로 실행한 방식 그대로. 집 로컬에서 이어서 계속하기 위한 번들.

## 핵심 (정직한 한계)
- arm A = 순수 LLM, arm B = **구조를 프롬프트로 근사한 PROXY**(실제 NKG·공식 엔진 아님).
- 판정자 = LLM(인간 작가 아님). 따라서 **방향성 신호**이며 G_VALUE_PROOF 자체가 아님.
- 첫 실행 결과: N=4 무승부(A 2:B 2), **길이 교란**(A 874자 vs B 557자) 발견.

## 사용한 설정 (정확히)
- 생성·판정 모델: `gemini-2.5-flash` (Anthropic·OpenAI 키는 잔액/쿼터 소진으로 미사용 → Gemini 사용)
- generationConfig: 생성 temp 0.8 / 판정 temp 0.2, `thinkingConfig.thinkingBudget=0` (thinking이 출력토큰 소진하는 문제 회피)
- max output tokens: A 750 / B 820 / 판정 600
- 블라인드: 씬별 seed(100+idx)로 작품1/2 순서 무작위, 라벨→arm 역매핑으로 승자 집계

## 실행
```bash
export GEMINI_API_KEY=<본인 키>          # 코드에 키를 넣지 말 것
rm -f results.jsonl
for i in 0 1 2 3; do python3 harness_one.py $i; done   # 씬당 생성2+판정1 호출, results.jsonl 누적
python3 aggregate.py                       # 집계 출력
```
- 모델 교체 시 `harness_one.py`의 `M=` 변경(예: gemini-2.5-pro, gemini-3-flash-preview).
- Anthropic/OpenAI로 돌리려면 호출부를 각 API 스펙으로 교체(키 잔액 필요).

## 다음 단계 (본 실험 G_VALUE_PROOF로 가기)
1. **길이 통제**: 양 팔 동일 목표 길이·동일 토큰예산. 구조 지시는 system 분리해 출력예산 잠식 방지.
2. **arm B = 실제 파이프라인**(NKG·공식·RAG). 프롬프트 프록시 아님.
3. **판정자 = 인간 작가 5+**. LLM 판정은 사전 스크리닝 보조만.
4. **N 확대 + 사전등록**(preregister.json: B 선호 ≥60%, p<0.05, 효과크기).
5. **검증 2**: 해석적 공식-Critic vs 블랙박스 보상모델 ablation.

## 파일
- `harness_one.py` — 씬 1개 실행(생성 A/B + 블라인드 판정 + 점수), results.jsonl 누적
- `aggregate.py` — 집계
- `results.jsonl` — 1차 실행 원자료(생성 4씬 전문 포함)
- `../docs/sessions/2026-06-02_value_proof_MVE_results.md` — 결과 리포트
