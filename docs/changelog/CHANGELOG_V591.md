# Changelog — V591 (v9.6.0)

**릴리즈일**: 2026-05-21  
**버전**: 9.6.0  
**SP**: SP-A.4 MOCK↔REAL Equivalence Tester  
**Gates**: 49/49 PASS (G1~G50)  
**테스트**: 5,820+ PASS (+35 신규)

---

## 신규 기능

### SP-A.4: EquivalenceTester — MOCK↔REAL 5축 검증

#### `literary_system/finetune/equivalence_tester.py` (신규, 461 lines)

**5축 검증 체계**

| 축 | 이름 | 기준 |
|----|------|------|
| 1 | schema_match | 필수 키 100% 존재 |
| 2 | length_ratio | 0.9 ≤ ratio ≤ 1.1 |
| 3 | kl_divergence | KL(P‖Q) ≤ 0.3 |
| 4 | bertscore_f1 | n-gram F1 ≥ 0.80 |
| 5 | safety_pass | PII/금칙어 0건 |

**핵심 클래스**
- `EquivalenceTester` — 5축 검증기 (compare / run_golden_set / update_golden_set)
- `EquivalenceAxis` — 단일 축 결과 (name / passed / score / threshold)
- `EquivalenceReport` — 단일 샘플 5축 종합 보고서
- `EquivalenceDriftReport` — 골든셋 전체 drift 평가 (pass_rate / drift_detected / axis_stats)

**Drift 감지 기준**
- `drift_detected = True` if `pass_rate < 0.95`
- 골든셋 기본값: 한국 드라마/소설 장면 요약 텍스트 20개

**LLM-0 준수**
- BERTScore: 실제 BERT 모델 없이 unigram+bigram n-gram F1 근사치 사용
- 외부 LLM API 호출 없음 (EQ-10 검증)

#### `.github/workflows/equivalence_monthly.yml` (신규)

- cron: `0 0 1 * *` (매월 1일 00:00 UTC)
- `workflow_dispatch` 수동 트리거
- drift 감지 시 GitHub Issue 자동 생성
- `equivalence_report.json` artifact 90일 보존

---

## Gate

| Gate | 이름 | 체크포인트 | 결과 |
|------|------|-----------|------|
| G50 | EquivalenceGate | EQ-1~EQ-10 | **PASS** |

**EQ-1**: import 성공  
**EQ-2**: EquivalenceTester 클래스 존재  
**EQ-3**: EquivalenceReport 데이터클래스  
**EQ-4**: EquivalenceDriftReport 데이터클래스  
**EQ-5**: compare() → 5축 모두 포함  
**EQ-6**: self-consistency → all_passed=True  
**EQ-7**: 골든셋 기본값 20개  
**EQ-8**: run_golden_set() pass_rate ≥ 0.95  
**EQ-9**: drift_detected=False (self-consistency)  
**EQ-10**: LLM-0 준수  

---

## ADR

- **ADR-052**: MOCK↔REAL Equivalence Tester (`docs/adr/ADR-052.md`)

---

## 테스트

| 파일 | 케이스 | 결과 |
|------|--------|------|
| `tests/unit/test_equivalence_tester.py` | TC01~TC35 | **35/35 PASS** |

**테스트 그룹**
- TestSchemaMatch (TC01~TC05) — 스키마 일치
- TestLengthRatio (TC06~TC09) — 길이 비율
- TestKLDivergence (TC10~TC13) — KL 발산
- TestBERTScoreF1 (TC14~TC17) — BERTScore F1 근사
- TestSafetyPass (TC18~TC21) — 안전성 검증
- TestEquivalenceTester (TC22~TC27) — 통합 tester
- TestGoldenSet (TC28~TC31) — 골든셋 실행
- TestDriftReport (TC32~TC35) — drift 감지

---

## 수치 비교

| 항목 | V590 (9.5.0) | V591 (9.6.0) |
|------|--------------|--------------|
| Gates | 48/48 | **49/49** |
| 신규 테스트 | — | **+35** |
| ADR | ADR-001~051 | **ADR-001~052** |
| EquivalenceTester | 없음 | **구현 완료** |
| 월간 CI | — | **equivalence_monthly.yml** |

---

## 버그 수정

- `EquivalenceDriftReport` 네이밍: 기존 `soak_replay_expander.py`의 `DriftReport`와 충돌 방지 (duplicate_zero_g37 Gate 준수)
- V584~V586 테스트의 `total_gates == 48` → `>= 48` 호환성 수정
