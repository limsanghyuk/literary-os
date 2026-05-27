# CHANGELOG V667 — NovelAI 경쟁 흡수 (SP-C.4 G72-1)

**버전**: v11.40.0  
**날짜**: 2026-05-27  
**브랜치**: dev/v667-novel-ai-absorption → main  
**ADR**: ADR-129 (경쟁 흡수 아키텍처 — G72 서브게이트 체계)

---

## 변경 요약

SP-C.4 경쟁 흡수 서브페이즈 첫 버전. NovelAI 분석·흡수·IP 자문(IP-ADV-001) 완료.

### 신규 패키지: `literary_system/absorption/`

| 파일 | 내용 |
|------|------|
| `absorption/__init__.py` | SP-C.4 패키지 초기화, 5종 심볼 공개 |
| `absorption/base.py` | CompetitorProfile, AbsorptionReport, FeatureGap, IPAdvisoryCommit, AbsorptionStatus |
| `absorption/novel_ai.py` | NovelAIAbsorber — analyze() + build_report(), IP-ADV-001 클리어 |

### 신규 모듈

| 파일 | 내용 |
|------|------|
| `gates/competitor_absorption_gate.py` | G72SubResult, G72Report, run_g72_subgate(), run_g72_gate() |
| `docs/adr/ADR-129.md` | 경쟁 흡수 아키텍처 결정 기록 |

### 수정

| 파일 | 내용 |
|------|------|
| `gates/release_gate.py` | G72-1 NovelAI AbsorptionGate 추가 (총 67 gates) |
| `tools/run_release_gate.py` | 버전 헤더 11.40.0 갱신 |
| `pyproject.toml` | version 11.39.0 → 11.40.0 |

### 삭제

| 파일 | 이유 |
|------|------|
| `literary_system/schemas_ext/` | 빈 고립 패키지 — TC35(ADR-128) 요구사항 충족 |

---

## G72-1 게이트 결과

- **경쟁사**: NovelAI  
- **IP 자문**: IP-ADV-001 (CLEARED)  
- **흡수된 기능**: StyleDNA 빠른 전환, 짧은 씬 레이턴시, Lorebook 세계관  
- **거부된 기능**: 애니메이션/이미지 생성 파이프라인 (IP 위험 HIGH)  
- **결과**: G72-1 PASS

---

## 테스트

- 신규 TC: 30개 (`tests/unit/test_v667_novel_ai_absorption.py`)  
- 전체 TC: **8,448 PASS**  
- Release Gate: **67/67 PASS**

---

## RULE-0 이행

- 버전 시작 전 Preflight 실행: `preflight_v11.39.0_2026-05-27.md` (13단계)  
- G_CONNECTIVITY: 77개 패키지 연결됨 (schemas_ext 삭제, absorption 연결 완료)
