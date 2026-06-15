# 집→회사 연속 핸드오프 v1.0 — 2026-06-15 (인간GT·char_ner·생성본체·LLM-1 진입)

> **다음 세션(회사 또는 집)이 이 문서 하나로 이어받기.** 현재 **집 로컬**에서 개발 중. 회사에서 이어갈 때 §9(환경) 먼저 확인.
> 진입 순서: 본 문서 → `docs/sessions/INDEX.md` → 해당 ADR/측정 보고서.

## 0. 한 줄
허브 정합·검증을 마친 뒤, 내가 지적한 "진짜 부족한 설계 3대 빈칸"을 코드로 메우고(**인간GT·char_ner·생성 Pass4~7**), 생성 본체를 실 LLM로 E2E 가동(Pass6 4/4·패널 4/4)한 다음, **LLM-1 Critic 레이어 진입(critic/, G_LLM1_BOUNDARY)** 까지 갔다. **V745(v13.0.0) → V754(v13.8.0)**.

## 1. 오늘 작업 전체 흐름 (3 국면)
**① 정합·검증** — GitHub 실상태 재확인(V571 멈춤은 캐시 착시; 실제 V745+), V745-PATCH1(RestrictedPython·biweekly_train·G77 ADR-145), 오리엔테이션/문서 V745 정합, **GitNexus V745 재인덱싱(41,586 심볼)**, V745 Phase D Exit G95 8/8 검증.
**② 진단·실측** — RAG(하이브리드 BM25+dense+RRF) / NKG(지식그래프) 구조 파악, **longform 실측**(공식=구조 게이트, arc 키워드 게임화·R 변별력 부재), 로컬 corpus_ko(205~395편 tri-store) 전수 학습, Phase E~G·P0~5·LLM-0~3 설계 전수 검토(3 에이전트), V749 코드↔문서 정합.
**③ 우선순위 개발 + LLM-1 진입** — 아래 §2.

## 2. 버전·커밋·태그 이력 (오늘 신규)
| 버전 | 커밋 | 태그 | 내용 |
|---|---|---|---|
| 정합 | 6610451 | — | RELEASE_INFO·README V745→V749 |
| (docs) | a86ad16 | — | 인간 GT 평가 프로토콜 L4 설계 |
| **V750** | 1df32ad | **v13.4.0** | `human_gt.py` + G_HUMAN_GT_ALIGNMENT (43 TC) |
| **V751** | 6fa61de | **v13.5.0** | `char_ner.py` 시리즈 NER (17 TC) |
| **V752** | 732a5be | **v13.6.0** | 생성 본체 `passes4_7.py` Pass4~7 (15 TC) |
| (docs) | 0154583 | — | Pass5 실 LLM E2E 실측 v1.0 |
| (docs) | e1395bc | — | Phase E.2 LLM-1 진입 설계 L4 |
| **V753** | 4df03ec | **v13.7.0** | `critic/base.py` 5축 + G_LLM1_BOUNDARY (27 TC, ADR-214) |
| **V754** | 3f56360 | **v13.8.0** | `critic/llm_critics.py` 5종 (24 TC, ADR-215) |
| (docs) | 5d405d0 | — | Pass5 E2E GPT-5 vs 4o-mini 비교 |
| (docs) | 93aa179 | — | Pass4/Pass7 실명작 재측정 로컬 스크립트+절차 |

## 3. 신규 코드·모듈
- **`literary_system/validation/human_gt.py`** (V750) — 인간 작가 쌍대 블라인드 평가: GTMode(A/B/C)·GTPair·GTRecord·`build_blind_sheet`·`inter_rater_alpha`(Krippendorff)·`panel_alignment`·`run_g_human_gt_alignment`(α≥0.6). DB 앵커 강제(LLM 회상 차단), 절대점수 금지.
- **`pipeline/char_ner.py`** (V751) — 시리즈 단위 NER 8단계(화자한정·장소제외 -실/방/관·≥2회차·친족분리·LLM폴백·char-scene 엣지). 드라마 166편 NOCHAR 해소용. `--selftest`.
- **`orchestration/passes4_7.py`** (V752) — Pass4 RAG결선·Pass5 초안(LLM주입)·Pass6 구조 sanity 게이트·Pass7 패널 쌍대보상 + 짧은 루프A. retrieve/generate/judge/reference_of 전부 주입형.
- **`literary_system/critic/`** (V753~754) — LLM-1 Critic 레이어. base(5축 STRUCTURE/CHARACTER/DIALOGUE/EMOTION/GENRE·CriticContext[RAG필수]·CriticVerdict[쌍대]) + llm_critics(5종 실 LLM critic·`evaluate_all_axes`). 합의=pairwise BT.
- **게이트**: `G_HUMAN_GT_ALIGNMENT`(human_gt) · `G_LLM1_BOUNDARY`(corpus/constitution/finetune 외부LLM 0건).

## 4. 측정 결과 (실 OpenAI)
- **longform**: 생성 산문 R 변별력 부재(ΔR=0.016), arc 마커 주입 0.25→1.0(게임화). → 공식=구조 게이트 강등.
- **Pass5 E2E(4o-mini)**: 4씬, **Pass6 4/4 PASS**, R평균 0.571, **Pass7 패널 4/4**. 비용 $0.0013.
- **GPT-5 비교**: Pass6 3/3, R평균 0.518(4o-mini보다 낮음 — 절제 산문을 공식이 못 잼), 14× 비용. → **공식은 모델 품질 비교에 부적합**(3번째 확증).
- **모델 가용**: gpt-5/5-mini/5-chat-latest 존재("5.5" 없음).

## 5. 설계 문서 (L4)
- `2026-06-15_human_gt_protocol_L4_v1.md` — 인간 GT 운영(5원칙·3모드·α·캘리브레이션).
- `2026-06-15_phase_E2_llm1_critic_entry_L4_v1.md` — LLM-1 진입(ADR 214~223 재배정·5 Gate·critic 12모듈·버전맵 V753~).
- `2026-06-15_pass5_e2e_measurement_v1.md` / `_gpt5_vs_4omini_v1.md` / `_pass4_pass7_local_remeasure_procedure_v1.md`.

## 6. 핵심 발견·교훈
1. **공식=구조 sanity 게이트, 품질=패널/인간GT** — longform·loop-B·Pass5·GPT-5 비교가 **4중 독립 확증**. 공식 R로 품질·모델 비교 금지.
2. arc는 키워드 게임화 가능 → 보상으로 쓰면 위험(게임화 가드 필요).
3. critic 프롬프트 'WINNER:' 형식 미준수 시 tie 기본처리 → **형식 강제·심판 상향 필요(V755)**.
4. 절대 검증은 여전히 **인간GT(작가)+실명작 레퍼런스** — 외부 의존.

## 7. 현재 진척 (P0~5 / Phase)
- P0/P1 무결성 ✅ · P2 데이터+GT ✅(인프라 완성, 작가 섭외 대기) · P3 공식검증 ✅ · **P4 생성본체 ✅(Pass1~7 배선)** · P5 UI 미착수.
- **Phase E.2(LLM-1) 진입 시작** — critic/base+5종 critic 완료. 다음 critic_ensemble·alignment.

## 8. 회사(또는 집)에서 이어받을 다음 순서
1. **V755**: critic 프롬프트 'WINNER:' 형식 강제 + 심판 상향(3페르소나/gpt-5). [본 모드, 코드]
2. **V756~759**: critic_ensemble(Pass7 승격)·alignment_monitor(human_gt 일치율·G_LLM1_ALIGNMENT)·corpus_gate(G_LLM1_SAFETY)·llm1_metrics(G_LLM1_COST). [본 모드]
3. **로컬 데이터 재측정**: emb_cache→ChromaDB·scene_features.db 복원 후 `orchestration/e2e_pass5_local.py` 실행 → **Pass4 실 RAG·Pass7 실명작 격차 실측**. [개발자 로컬]
4. **char_ner 실행**: 로컬 `python pipeline/char_ner.py` → 드라마 166편 NOCHAR 해소, nkg.json 재생성. [개발자 로컬]
5. **작가 베타 2~3명 섭외** → human_gt 1차 라운드 → loop-C 학습신호. [개발자]
6. 개발자 결정 잔여: D-E2-3(비용 상한 $50).

## 9. 환경 주의 (집↔회사 연속)
- **매 버전 RULE-0**: `python3 tools/run_preflight.py` PASS 후 착수(자동 집행).
- **키**: `OPENAI_API_KEY` 환경변수 전용(코드/로그/커밋 비노출). Anthropic 미충전·Gemini 소진, **OpenAI 가용**.
- **로컬 데이터**: corpus_ko verbatim은 로컬 전용(허브 비커밋). 회사에서도 `Scripts.zip`/`emb_cache` 복원 필요(DATA_INTEGRITY_NOTE).
- **FUSE 주의**: ChromaDB/SQLite는 마운트서 disk I/O error → 로컬 디스크 빌드 후 export. 영속 원천=emb_cache.
- **docs/sessions는 .gitignore** → 신규 문서 `git add -f` 필요.
- **매 버전 완료 시 통합 ZIP 제공**(개발자 요청): `C:\claude\literary-os-vNNN.zip`.

## 10. 재현 도구·위치
- 게이트: `tools/run_human_gt_gate.py` · `tools/run_llm1_boundary_gate.py` · `tools/run_pairwise_gates.py`
- 생성 E2E: `orchestration/{passes,passes4_7,e2e_pass5,e2e_pass5_local}.py`
- 파이프라인: `pipeline/char_ner.py`
- 통합본: `C:\claude\literary-os-v754-final.zip` (v13.8.0)
