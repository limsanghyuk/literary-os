# 세션 정리 — 2026-06-02 (Claude 기획·설계 모드)

본 세션에서 수행한 작업을 시간순으로 정리. 집 로컬 환경에서 이어가기 위한 인계 문서.

## 0. 커밋 이력 (허브 main)
| 단계 | HEAD | 내용 |
|---|---|---|
| 시작 | 2b3c3bc | Phase E 보고서 v1.1 |
| 1 | 5536758 | Phase E~G 통합 기획 보고서 v1.0 + 핸드오프 |
| 2 | 96f85eb | Phase E 검증 우선 제안서+설계도+핸드오프 |
| 3 | (본 push) | 검증 실험 번들 + 본 세션 정리 |

## 1. 이전 세션 조사
- "Model evolution plan 411 to 420" 세션 정독 → 실제는 Phase E 기획 논의(Claude Design, LLM-1 전환 등).
- 개발자 허브 = **github.com/limsanghyuk/literary-os**. 로컬 `C:\literary_claude\claude` = 버전 zip 릴리즈 아카이브.

## 2. 로컬 정리 (릴리즈 위생)
- zip 107개(595MB) 무결성 검증: SHA256 PASS 22/22.
- 보존정책 적용: 마일스톤 31개 유지, 조밀증분 76개(424MB)를 `_zip_archive/`로 가역 격리. `RETENTION_POLICY.md`·`cleanup_archive.ps1` 생성.
- stale 추출본 `literary-os/`(v10.4.0/V599)에 `_STALE_DO_NOT_USE.md` 마커(허브가 신뢰기준).

## 3. V745 무결성 검증 (→ SP-E.0 선결과제)
- 내부 SHA256SUMS.txt 971항목: 정상 883 / 미패키징 35 / **해시불일치 53**.
- 53건 = phase-d-exit 막판 패치셋(release_gate.py·pyproject.toml·test_inventory.json·finetune/*·constitution/*). 즉 **막판 패치 후 매니페스트 미재생성** = 릴리즈 자기검증 불가(코드 손상은 아님).
- test_inventory.json stale(05-25<05-29). ADR 결번 37·38(실누락)/83~87·126·127(추정 결번).
- 조치: SP-E.0(TD-E0-1 매니페스트 재생성 강제 게이트 / TD-E0-2 inventory 자동화 / TD-E0-3 ADR 정합).

## 4. Phase E~G 통합 기획 v1.0 (HEAD 5536758)
- 축: LLM-0→LLM-2.5 점진 완화(공식=sanity baseline 잔존).
- E(V746~795,LLM-1): SP-E.0→E.1 코퍼스50→E.2 LLM-1(10 ADR·5 Gate·12 모듈·5축)→E.3·E.4 병렬→E.5.
- F(V796~875,LLM-1.5): Critic 5축 전체 AI+생성 초안만 완화+코퍼스200·다언어.
- G(V876~955,LLM-2.0~2.5): 생성 주력+자율 평가루프+B2B SaaS 매출.
- 결정 D1~D15(개발자 대기). 권고: 생성완화=초안만, 자금=정부R&D+스튜디오(VC 보류).

## 5. 모델 가치 평가 (vs 상용)
- 상용(Sudowrite Story Bible / NovelCrafter Codex)도 '구조+LLM'으로 수렴 중. 장편 일관성은 업계 미해결 난제.
- Literary OS 차별점: 더 깊은 구조(NKG·공식·게이트)·감사가능성·도메인 특화·B2B 적합.
- 약점: 코퍼스 실데이터 0·LLM 미연결(LLM-0)·UI 없음·실산출물 없음. **현재 실현가치 낮음, 잠재가치 높음.**
- 핵심: "구조+LLM이 순수 LLM보다 독자선호 우위"가 미검증 → 이게 분기점.

## 6. 공식 관점 재정의 (개발자 지적 반영)
- 공식 = LLM 대체가 아니라 **학습 가능한 해석적 prior/Critic**(AI 약점 교정 가드레일). 계수는 학습으로 진화.
- 근거(V745 실측): `learning/physics_coefficient_updater.py`(gradient, lr 0.01), `optimizer/update_coordinator.py`(공식↔학습 store 동기 게이트) 이미 존재.
- ML 주류(reward/critic/RLAIF/verifier)와 정합.

## 7. 검증 우선 제안서+설계도 (HEAD 96f85eb)
- Phase E 종료게이트를 **G_VALUE_PROOF**(블라인드 작가 선호 실험)로 격상, MVE(V774~775) 삽입.
- 공식을 LearnableCritic으로 명세(오류수정·계수갱신 루프). 두 겹 검증(구조>순수 / 공식 vs 보상모델).
- 결정 D16~D20.

## 8. PROXY-MVE 실제 실행 (본 세션 핵심)
- 환경: Gemini 2.5 Flash(Anthropic·OpenAI 키 잔액/쿼터 소진). 동일 프롬프트 4씬 × A(순수)/B(구조프롬프트) 실생성 + 블라인드 LLM 판정.
- **결과: N=4 무승부(A 2:B 2), 총점 A 17.5 vs B 15.8, 길이 교란(A 874 vs B 557자) 발견.**
- 해석: 얕은 프록시로는 우위 없음 → 깊은 파이프라인+인간평가+길이통제+충분한 N으로 본 실험 필요. 하니스는 실작동 입증.
- 재현 코드: `experiments/value_proof/` (harness_one.py·aggregate.py·README.md·results.jsonl).

## 9. 집 환경 인계 (다음)
1. `experiments/value_proof/README.md` 절차대로 본인 키로 재실행(길이통제판부터 권장).
2. 결정 D1~D20 확정 → Phase E 본안(blueprint) 작성.
3. SP-E.0 무결성 보강은 결정 무관 즉시 착수 가능.

## 보안 기록
- 사용한 4개 키(GH PAT·Claude·GPT·Gemini)는 환경변수 전용·마스킹·사용 후 unset. 커밋/문서/채팅에 키 노출 0건. Anthropic·OpenAI 잔액 소진 상태 확인.
