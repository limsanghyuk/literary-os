# corpus_ko — 한국 시나리오 실데이터 구축 리포트 (2026-06-13)

**원천**: 개발자가 합법 입수해 `C:\claude\Scripts`에 적재한 한국 영화/드라마 대본.
**원칙**: eval-only, verbatim 원문은 허브에 **비커밋**(로컬 작업폴더에만 존재). 임베딩·피처·그래프 등 파생물만 분석에 사용.

## 1. 파이프라인 (쿼리/스키마/청크/JSON/마이그레이션/ChromaDB RAG)

```
입수 대본(hwp3/hwp5/doc/docx/pdf)
  └─[변환 라우팅]─ HWP5→hwp5txt · HWP3/doc/docx→LibreOffice · pdf→pdftotext
      └─ txt/ (106편 정상)
          └─[씬 파싱] 번호헤딩(S#/#/N./씬) + 슬러그(실내·실외·낮·밤) + 폴백블록
              └─ scenes/*.jsonl (9,543 씬)
                  └─[듀얼 청킹] 씬청크 + 슬라이딩(1000/200)
                      └─ chunks/*.jsonl (18,358 청크)
                          └─[임베딩] OpenAI text-embedding-3-small (1536d)
                              └─ emb_cache/ (92 샤드 = 재구축 원천)
                                  └─[마이그레이션 → tri-store]
                                       ├─ ChromaDB  : ko_scenes 10,653 + ko_slides 7,705 (cosine RAG)
                                       ├─ SQLite    : scene_features.db (9,543 행)
                                       └─ NKG graph : nkg.json (NEXT 9,437 · 인물 400 · 인물-씬 4,681 · 공기 pairs)
```

## 2. 산출물 인벤토리

| 산출물 | 위치 | 규모 |
|---|---|---|
| 변환 텍스트 | `corpus_ko/txt/` | 106 works |
| 씬 JSONL | `corpus_ko/scenes/` | 9,543 scenes |
| 청크 JSONL | `corpus_ko/chunks/` | 18,358 chunks |
| 임베딩 샤드 | `corpus_ko/emb_cache/` | 92 shards (재구축 원천) |
| ChromaDB 익스포트 | `corpus_ko/chroma_export.tar.gz` | 185MB, 18,358 vectors |
| SceneFeature DB | `corpus_ko/scene_features.db` | 9,543 rows |
| NKG 그래프 | `corpus_ko/nkg.json` (+`nkg_summary.json`) | 106 works |
| 매니페스트 | `corpus_ko/manifest.json` | — |

## 3. SceneFeature (공식 F-07~F-10 정량화 연료)

각 씬당 산출 — `conflict_intensity`(갈등 어휘 밀도), `scene_energy_ratio`(문장부호+짧은행 템포),
`motif_residue_score`(임베딩 기반: 이전 씬들과의 평균 코사인 = 모티프 잔향),
`curiosity_gradient`(직전까지 최대유사 대비 신규성 = 호기심 도약), `dialogue_ratio` 등.
코퍼스 평균 conflict 0.335 / energy 2.419 / motif 0.466 / curiosity 0.337.

## 4. Tier-1 50편 커버리지: 17 확보

확보: 올드보이·살인의추억·마더·박쥐·곡성·밀양·추격자·신세계·부당거래·달콤한인생·친절한금자씨·공동경비구역JSA·광해·택시운전사·부산행·괴물·타짜.
이외 비-Tier1 양질 89편(2000년대 중심: 비열한거리·라디오스타·우아한세계·음란서생·넘버3·엽기적인그녀·클래식 등) 포함 → 총 106편.

## 5. 미변환 잔여 (12편)

- **이미지 PDF(8)** OCR 필요(한국어 traineddata 부재로 샌드박스 처리 불가): 감시자들·검은사제들·과속스캔들·그때그사람들·범죄의재구성·변호인·작전·홍당무
- **손상 HWP(1)**: 연애의목적 (hwp5txt 0바이트)
- **RAR(1, 멀티파트)**: 황해 (unrar/7z 미설치)

## 6. 기술 메모

- ChromaDB·SQLite는 FUSE 마운트에서 `disk I/O error`(SQLite 락 미지원) → **로컬 디스크에서 빌드 후 마운트로 export**. 영속 원천은 `emb_cache` 샤드(언제든 재구축).
- 임베딩·청킹·파싱 스크립트: `corpus_ko/{convert,parse,embed,store_chroma,features,nkg}.py` (모두 멱등·재개 가능).

## 7. 다음 단계 (검증·자가학습)

데이터가 처음으로 충분해짐 → FE-1~8(전부 쌍대) 실행 가능. 특히 **★FE-7**(공식 점수 vs 전문가+관객 메타-GT),
DRSE 잔향 검증(motif_residue 실측 정렬), F-24/25 장르별 긴장곡선(scene_energy 시퀀스), 공식↔Critic 학습 루프 1차.
