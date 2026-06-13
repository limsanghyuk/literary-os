# ★ 세션 마스터 인덱스 — 2026-06-13 (회사→집 연속용)

> 다음 세션(집)은 **이 문서 하나로 전부 파악**. 허브 `docs/sessions/2026-06-13_corpus_ko_build/`.

## 0. ⚠️ 데이터 물리 위치 (가장 중요 — 반드시 읽기)
| 자산 | 위치 | 허브에 있나 |
|---|---|---|
| 원본 대본(영화·드라마) | **로컬**: `C:\claude\Scripts\` + 작업폴더 | ❌ (verbatim 비커밋) |
| 변환 텍스트·씬·청크 | **로컬**: 작업폴더 `corpus_ko/{txt,scenes,chunks}` | ❌ |
| 임베딩(261샤드)·ChromaDB·SceneFeature DB | **로컬**: `corpus_ko/{emb_cache,chroma_export.tar.gz,scene_features.db}` | ❌ (용량·verbatim파생) |
| **코드·리포트·집계JSON·설계·제안서** | 로컬 + **허브** | ✅ |

**결론**: 물리적 실데이터(395편 tri-store)는 **로컬(회사 머신)에만** 있다. **허브에는 데이터가 없고 코드·결과·설계만** 있다.
**회사→집 전환**: 허브로는 *기획·코드·결과의 연속성*만 넘어간다(집에서 이해·설계·재구축 가능). **실데이터로 작업하려면**:
- (A) 작업폴더 `...\literary\corpus_ko\` 전체(+`C:\claude\Scripts`)를 **물리 복사**(USB/클라우드) → 집에서 즉시 사용, 또는
- (B) 집에서 대본 재입수 → 파이프라인 재실행(재변환·재임베딩, OpenAI ~$0.5). 임베딩 원천 `emb_cache`만 복사해도 재임베딩 생략 가능.
**오늘 조치**: 소멸성이던 임베딩(샌드박스 emb2 311M)을 작업폴더 `emb_cache`(261샤드)로 복사해 **durable화**했고 ChromaDB도 재익스포트(231M). 즉 작업폴더는 자족적이다(회사 머신 한정).

## 1. 오늘 한 일 (한눈에)
실 시나리오 **0편 → 395편 tri-store** 구축 + 공식 검증 7실험 + 패널 + 자율루프 2실험(음성) + 생성본체 착수 + 보강 제안서.

## 2. 데이터 (corpus_ko, 멱등 파이프라인 `convert/parse/embed/store_chroma/features/nkg.py`)
- **395편 / 31,225씬 / 청크 51,996 / ChromaDB 51,996벡터(scene 32,813+slide 19,183) / SceneFeature 31,225행 / NKG**.
- 영화 ~95(2000s~2010s) + 드라마 24시리즈 ~300회(신사의품격·태양의후예·궁·역전의여왕·옥탑방고양이·별순검·장밋빛인생·적도의남자 등).
- 보류: rar(열여덟스물아홉)·이미지PDF 8·손상hwp 1.

## 3. 실험·검증·결과 (experiments/, 전부 쌍대·정직)
| 실험 | 결과 | 문서 |
|---|---|---|
| ★FE-7 v2 (권위 메타GT) | fitness_v2 vs (관객+전문가) **τ+0.196 conc 0.60**. thematic_complexity 최강(0.195). 관객>수상 | FE7v2_DRSEv2_RESULTS |
| 학습루프 LOO-CV | 0.594(등가중≈적합) | 〃 |
| EXP-C 장르곡선 | 장르별 뚜렷 구분(L1 0.286) | EXP_REPORT |
| ★드라마 장르곡선 | **드라마=클리프행어 end-high, 영화=해소 end-low** 실증 | DRAMA_ANALYSIS |
| DRSE 모티프사전(mecab) | 잔향 위치상관 **0.009→0.70**. 콜백 타이밍 반전(neat payoff=비명성) | REDEFINE, MECAB_LOOPB |
| 패널 변별력 POC | **73%(만장일치 82%)** | POC_PANEL |
| ★★루프B(작품/씬 2회) | **둘 다 실패(40%/44%)** → 입자도 아닌 *피처 종류*가 문제 | SCENE_LOOPB |

## 4. 문제점 → 해결책 (오늘 도출, 핵심)
1. **공식이 명성과 약상관** → 성분분해로 conflict·thematic만 유효 신호 식별 / energy·motif·climax는 재정의·demote. **fitness_v2 확정**.
2. **DRSE 임베딩기반 무력(0.009)** → **재등장 모티프 사전(mecab 명사)**으로 재설계 → 0.70. (해결)
3. **루프B(공식이 패널 모사) 실패** → 원인=SceneFeature(표면통계)≠패널 craft. **해결책=중간루프B 폐기, 공식=구조게이트·패널=직접보상으로 자율루프 재배선.**
4. **NKG 인물 166편 NOCHAR + 장소누출** → **시리즈단위 NER 제안서**(화자위치 한정+헤딩제외+접미규칙+LLM 시리즈폴백). 프로토타입 실증. (제안 구비, 구현 대기)
5. **이미지PDF·rar** → OCR(한국어)·unrar 도구 확보 문제(데이터/도구).

## 5. 설계 확정·산출
- **자율 학습루프**(AUTONOMOUS_LOOP_v1 + SCENE_LOOPB): 공식=sanity 게이트, 패널=보상(루프A+C), 중간루프B 폐기. 불변식5(쌍대·실대본앵커·생성기≠심판·객관캘리브·인간체크).
- **생성 본체 L4**(GENERATION_BODY_L4_v1) + **착수**(orchestration/: schema·pass1~3·demo, 장르곡선 T_ideal 결선 동작).
- **보강 제안서**(CHAR_NER_PROPOSAL): 인물 NER 8단계 + DoD.
- **완성도**(MASTER_STATUS): P2·P3 L4, P4 L3.7(생성착수), 다음=Pass4~7.

## 6. 다음 세션(집) 진입 순서
1. 본 인덱스 → SESSION_HANDOFF → MASTER_STATUS → 메모리 `project_formula_validation_exp1.md`.
2. **데이터 확보**: (A)작업폴더 복사 or (B)재구축(emb_cache 있으면 재임베딩 생략).
3. **본류**: 생성 Pass4~7 구현(소넷) + **드라마 장르곡선(end-high) Pass3 결선**.
4. **병행 보강**: NKG 인물 시리즈 NER(제안서대로) — 생성 Pass3/4 입력이므로 선결.
5. **데이터/도구**: 드라마 시청률 메타GT 취합(드라마 FE-7 개통), OCR/unrar.

## 7. 파일 지도 (허브 docs/sessions/2026-06-13_corpus_ko_build/)
- 루트: `SESSION_HANDOFF`·`manifest.json`·`BUILD_REPORT`·QC/sources/nkg_summary JSON
- `pipeline/`: convert·parse·embed·store_chroma·features·nkg·llm_chars
- `experiments/`: run·exp_cbd·exp_d·meta_gt(v1/v2)·motif_drse(v2)·poc_panel·loop_b·scene_loop_b·drama_genre_drse·char_ner_proto + 리포트 md들(EXP/FE7v2/REDEFINE/MECAB_LOOPB/SCENE_LOOPB/DRAMA_ANALYSIS/POC_PANEL/MASTER_STATUS/CHAR_NER_PROPOSAL/AUTONOMOUS_LOOP/GENERATION_BODY_L4)
- `orchestration/`: schema·passes·run_demo·demo_output

## 8. 허브 커밋 이력(오늘)
e4424ac→855fac4→fb7b9d6→3c7adc3→ef4503a→45d4818→76a2649→756204b→9b9e270→(본 인덱스).
