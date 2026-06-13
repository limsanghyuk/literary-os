# 세션 종합 핸드오프 — corpus_ko 구축·검증·생성착수 (2026-06-13)

> 다음 세션이 이 문서 하나로 "무엇이 있고, 무엇을 알았고, 무엇을 다음에 하는지" 파악하도록 작성. 모든 산출물은 `literary\corpus_ko\`(로컬, verbatim 비커밋) + 허브 `docs/sessions/2026-06-13_corpus_ko_build/`(코드·리포트·집계 JSON만).

## 0. 한 줄
실 시나리오 0편 병목을 **205편 tri-store**로 해소하고, 공식 4종 검증 + 패널 + 자율루프 2종 실험(음성 포함)으로 **"공식=구조 게이트, 패널=품질 보상"** 아키텍처를 실증 확정한 뒤, **생성 본체 Pass1~3 동작 골격을 착수**했다.

## 1. 데이터 (tri-store, 멱등 파이프라인)
- **205편 / 18,802씬 / ChromaDB 32,825벡터(scene 20,116+slide 12,709) / SQLite SceneFeature 18,802행 / NKG(NEXT·인물·공기쌍)**.
- 영화 ~95편(2000s~2010s) + 드라마: 신사의품격20·태양의후예16(전회 PDF)·알게될거야19·위대한유산17·장밋빛인생24·적도의남자18·두번째프러포즈22·강적들·귀여운여인.
- **보류**: 열여덟스물아홉(rar, unrar 부재) / 이미지PDF 8편(한국어 OCR data 부재) / 연애의목적(손상hwp).
- 파이프라인(`corpus_ko/*.py`, 전부 멱등·재개): `convert.py`(HWP5→hwp5txt·HWP3/doc/docx→soffice·pdf→pdftotext) → `parse.py`(번호헤딩+슬러그+폴백) → `embed.py`(OpenAI text-embedding-3-small 1536d, emb_cache 샤드=재구축원천) → `store_chroma.py`(로컬빌드후 chroma_export.tar.gz; FUSE sqlite 이슈 회피) → `features.py` → `nkg.py`+`llm_chars.py`(정규식+LLM 인물).
- ⚠️ **함정 기록**: ① cowork 폴더를 C:\claude\Scripts로 연결 시 virtiofs 하위폴더 못 열어 bash 부팅 깨짐→연결 해제 필요(데이터는 File Explorer로 작업폴더에 복사 후 처리). ② ChromaDB/SQLite는 FUSE 마운트서 disk I/O error→로컬디스크 빌드 후 export. ③ 신규 드라마 입수 시 작업폴더 복사→`convert/parse/embed/store/features/nkg` 순 재실행이면 자동 편입.

## 2. 검증 실험 결과 (experiments/, 전부 쌍대·정직)
- **★FE-7 v2**(`meta_gt_v2.py`,`run.py`): 권위 메타GT(전국관객수+수상). fitness_v2(conflict_mean+conflict_arc+thematic_complexity+curiosity) vs (관객+전문가) **τ+0.196 concordance 0.60**(이전 잠정 −0.06). **thematic_complexity 최강 τ0.195**. 관객(0.16)>수상(0.085).
- **학습루프 LOO-CV**: 0.594(등가중≈적합, 과적합0).
- **EXP-C 장르곡선**(`exp_cbd.py`): 장르별 긴장곡선 형태 뚜렷 구분(L1 0.286). thriller=초반피크, crime/drama=후반상승, comedy=후반빌드, melo=중반정점, romance=결말급강. → F-24/25 T_ideal 장르분리 실증(생성 Pass2에 결선됨).
- **DRSE v3**(`motif_drse_v2.py`, mecab 명사): 잔향 위치상관 **0.702**(임베딩 0.009→대폭개선). **콜백 타이밍 반전신호**: climax_payoff(후반 깔끔회수) τ−0.142 → neat payoff=비명성(작가영화 모호결말). 모티프 *양*은 명성 무관.
- **패널 POC**(`poc_panel.py`): 명성차 씬쌍 3역할 패널 **73%(만장일치 82%)** 변별. 인간작가 대체가능(객관사실 캘리브레이션 프록시).
- **★★루프B 2회 음성(중대)**: 작품수준(`loop_b.py`) 40% / 씬수준(`scene_loop_b.py`) LOO-CV 44%. **granularity가 아니라 피처 종류가 문제** — SceneFeature(표면통계)는 패널 craft와 무관/역상관(dialogue 16%·conflict 34%). **결론: "공식이 패널을 모사 학습"은 현재 피처로 불가→중간루프B 폐기.**

## 3. 설계 확정 (핵심 교훈)
- **자율루프 재배선**(`AUTONOMOUS_LOOP_v1.md` + `SCENE_LOOPB_RESULTS.md`): 공식=**구조 sanity 게이트만**(갈등존재·길이·tension_band·콜백 충족), 패널=**직접 보상**(짧은루프A 게이트 + 긴루프C 생성기 RLHF). 중간루프B(공식 모사)는 폐기/보류.
- **공식 진단**: 망가진 게 아니라 *구조*를 재고 *품질*을 안 잼. 검증된 신호=conflict(밀도+동역학)·thematic_complexity·장르곡선·DRSE구조. 약한 것=energy·raw motif·씬fitness as 품질(demote). → 설계철학(공식=baseline sanity check) 재확인.
- **옛 드라마 가치**: 구조학습·검증GT엔 오히려 강점(서사문법은 시대불변, 관객수·수상 안정). 한계는 동시대 스타일/트렌드뿐(나중 최신 소량 보강).

## 4. 생성 본체 착수 (orchestration/, 이번 신규)
- `schema.py`: WorkSpec / Beat / SceneBrief 계약(dataclass).
- `passes.py`: **pass1_premise**(거시설계) · **pass2_causality**(7기능 아크 비트맵, plant/payoff 모티프 분배, **EXP-C 장르곡선 T_ideal 결선**) · **pass3_scene_brief**(tension_band·callback·인물 결선).
- `run_demo.py` → `demo_output.json`: 프리미스 "균열"(thriller) → WorkSpec→7Beat→7SceneBrief 동작 확인.
- **미구현(다음)**: Pass4 RAG(ChromaDB+NKG+DRSE 사전 결선) · Pass5 초안생성(LLM) · Pass6 **씬-게이트**(구조 충족만, 품질판정 아님) · Pass7 패널보상. slug/location은 현재 TBD(LLM/RAG 채움 훅).

## 5. 개발 진척 (P0~5 × Phase E~G)
| | 항목 | 상태 | 근거 |
|---|---|---|---|
| P0/P1 | 무결성 | L4 | 개발자 완료 |
| **P2** | 데이터+GT | **L4** | 205편 tri-store + 권위 메타GT |
| **P3** | 공식 검증 | **L4(1차완결)** | FE-7·장르곡선·DRSE·패널·루프B 전부 실행+결론 |
| **P4** | 코어/생성 | **L3.7(착수)** | 생성 Pass1~3 동작골격. Pass4~7 미구현 |
| P5 | UI/개입 | L3 | 미착수 |
| Phase E | 검증기+본대 | **가동 가능** | 데이터·패널·게이트 확보 |
| F/G | | L3 | 설계 |

**종합**: 평가·검증 라인은 사실상 완결(P2·P3 L4). 남은 본류는 **생성 본체 Pass4~7 구현**(P4)과 P5 UI. 기획·설계는 충분(추가 기획 한계효용 낮음) — 이제 *구현*과 *동시대 스타일 소량 보강*의 영역.

## 6. 다음 세션 진입 순서
1. 본 문서 + `experiments/MASTER_STATUS_2026-06-13.md` + 메모리 `project_formula_validation_exp1.md` 읽기.
2. **우선 추천 = 생성 본체 Pass4~7 구현**(소넷 집행). Pass4=rag/hybrid_retriever+ChromaDB 결선, Pass6=씬 구조게이트, Pass7=poc_panel 승격.
3. 보조: 씬 craft 피처 연구(루프B 재생 조건) / rar 도구 확보 후 열여덟스물아홉 편입 / 동시대 최신작 소량.
4. 신규 대본 입수 시: 작업폴더 복사 → 파이프라인 재실행으로 자동 편입.

## 7. 허브 커밋 이력(이번 세션)
e4424ac(빌드+QC) → 855fac4(패널POC+재정의+자율루프+완성도) → fb7b9d6(권위GT FE-7v2+DRSE사전) → 3c7adc3(mecab+루프B음성+생성L4) → ef4503a(씬루프B+드라마8편 205편) → (본 핸드오프).
