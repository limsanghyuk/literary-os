# Claude (Home PC) Session — 2026-05-19

## 메타데이터

| 항목 | 값 |
|---|---|
| 일자 | 2026-05-19 |
| 환경 | 집 컴퓨터 · Claude Desktop (Cowork mode) |
| AI | Claude (Opus 4.7) |
| 페어 AI | Chief Architect × Chief Compiler × CSPE (3인 전문가 페르소나) |
| 기반 입력 | V574 Principal Engineer Report · V400 Preflight Guide v1.1 · GitHub V571 main 교차 검증 |
| 합의 결과 | docs/proposals/ 아래 4 docx + 2 README + 1 INDEX |

## 산출물

### 1. Phase 3 (V451~V480) 합의안 v2.0  (2026-05-15 작성, 2026-05-19 GitHub 정리)
- `docs/proposals/phase3_v451_v480/PROPOSAL_v2.docx`
- `docs/proposals/phase3_v451_v480/DESIGN_v2.docx`

### 2. V575~V580 안정화 합의안 v2.0  (2026-05-19 신규)
- `docs/proposals/v575_v580_stabilization/PROPOSAL_v2.docx`
- `docs/proposals/v575_v580_stabilization/DESIGN_v2.docx`
- `docs/proposals/v575_v580_stabilization/V574_Principal_Engineer_Report.docx` (참조용)

## 작업 워크플로우 (3인 전문가 페르소나)

```
Chief Architect (CA) + Chief Compiler (CC)
   ↓ V574 보고서 비판 — 20개 결함 가설 트리(Tree-of-Defects)
   ↓ Tree-of-Thought 3대 전략 평가
   ↓ 최적안 선정 (전략 B+ 혼합형)
Chief System Principal Engineer (CSPE)
   ↓ 13개 추가 합의 항목 (CSPE-A 추가/B 문제/C 해결책)
3인 최종 합의
   ↓ v2 제안서 docx 작성
   ↓ v2 설계도 docx 작성
   ↓ 자가 점검 (잔존 약점 W-01~W-05)
완성
```

## 회사 PC에서 이어 진행할 항목

다음 순서로 회사 PC에서 작업한다 (Preflight Guide v1.1 §3 12단계 의무 적용):

1. **세션 시작 시**:
   ```bash
   cd ~/work/literary-os   # 회사 PC 클론 경로
   git fetch origin
   git checkout main && git pull
   git checkout -b dev-company   # 최초 1회만
   # 또는: git checkout dev-company && git pull
   ```

2. **본 핸드오프 문서 확인**:
   ```bash
   cat docs/sessions/2026-05-19_claude_home_session.md   # 이 파일
   cat docs/proposals/INDEX.md
   cat docs/proposals/v575_v580_stabilization/README.md
   ```

3. **V574.1 즉시 핫픽스 0.5일 실행**:
   - DEV_MODE 기본값 → false (`apps/studio_api/auth/middleware.py:29`)
   - pyproject.toml description → V574
   - README.md badge → 7.9.0
   - CI ruff 추가 (.github/workflows/ci.yml)
   - tools/check_version_consistency.py 신규 작성
   - **검증**: Preflight Step 10 + 12만 실행 (위험도 G)

4. **V575 진입 전 Preflight**:
   ```bash
   python -m compileall literary_system/ -q
   python tools/run_release_gate.py
   pytest tests/ -k gate -q --tb=short
   ```

5. **V575 작업 시작** — 자세한 모듈 변경 목록은 `docs/proposals/v575_v580_stabilization/DESIGN_v2.docx §3`

## 핵심 합의 사실 (TL;DR)

- V574에 Critical 4건 + High 6건 존재 → V574.1 핫픽스(0.5일) + V575~V580 7주에 해소
- 새 Gate 8개 신설: G32~G39
- 새 ADR 7건 신설: ADR-032 + ADR-034 ~ ADR-039
- GATE_REGISTRY.py 단일 소스화로 README ↔ release_gate.py 영구 정합
- LLM 어댑터 canonical: `literary_system/llm_bridge/providers/{claude,openai,ollama}.py`
- mypy 5단계 점진 strict (Stage1 V576 → ... → Stage5 Phase 7)
- 커버리지 88% → 90% → 92% → 95% 점진 게이트
- multiwork 패키지 dead 여부는 V577 첫 1일 import 그래프 검증으로 결정

## 다음 결정이 필요한 사항 (회사 PC 작업 시 참고)

- multiwork 패키지 dead 판정 결과에 따라 V577 범위 변동 가능
- mypy Stage 3 도입 시 5,000+ 테스트 회귀 발생 시 Stage 후퇴 가능 (ADR-035)
- 성능 -5% 게이트가 너무 엄격할 경우 95% 신뢰구간으로 완화 가능
- ADR 1~13 자동 추출이 50% 미달 시 V580에서 Phase 7로 이연 가능

## 변경/푸시 이력

```
2026-05-19 [home pc / claude]
  + docs/proposals/INDEX.md
  + docs/proposals/phase3_v451_v480/{PROPOSAL_v2.docx, DESIGN_v2.docx, README.md}
  + docs/proposals/v575_v580_stabilization/{PROPOSAL_v2.docx, DESIGN_v2.docx,
                                            V574_Principal_Engineer_Report.docx,
                                            README.md}
  + docs/sessions/2026-05-19_claude_home_session.md (이 파일)
```
