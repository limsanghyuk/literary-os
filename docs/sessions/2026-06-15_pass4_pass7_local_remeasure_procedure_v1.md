# Pass4 RAG · Pass7 실명작 재측정 절차 (c) v1.0 — 개발자 로컬 실행

**작성일**: 2026-06-15 · **기준선**: main (V754~) · **문서 ID**: LOS-LOCAL-REMEASURE-PROC-V1.0-2026-06-15
**이유**: 샌드박스엔 corpus_ko verbatim 데이터가 없어 본 모드가 직접 실행 불가. 스크립트·절차를 제공하니 개발자 로컬에서 실행.

## 0. 무엇이 달라지나
이전 E2E(2026-06-15)는 **Pass4=스텁(검색 없음)·Pass7=열화-자기(실명작 아님)** 였다. 본 절차는:
- **Pass4** → 실 ChromaDB(ko_scenes)에서 유사 실제 씬 결선.
- **Pass7** → 생성 씬을 **실제 명작 씬(scene_id)** 과 쌍대 비교(진짜 절대 검증).

## 1. 필요 로컬 데이터 (3종)
| 데이터 | 용도 | 준비 |
|---|---|---|
| **ChromaDB (ko_scenes 컬렉션)** | Pass4 유사 씬 검색 | `chroma_export.tar.gz` 해제 **또는** `emb_cache`에서 `store_chroma.py` 재생성 |
| **scene_features.db** | (선택) 피처 질의 | `emb_cache`에서 `features.py` 재생성 |
| **scenes/*.jsonl** | Pass7 실명작 레퍼런스 본문 | 이미 로컬 보유(무손상) |

> DATA_INTEGRITY_NOTE 대로 **scene_features.db(0바이트)·chroma_export(잘림)는 emb_cache 261샤드에서 재생성**. 스크립트 경로의 `/sessions/...` 를 집 로컬 경로로 치환.

## 2. 복원 (집 1회)
```bash
# corpus_ko 작업폴더에서
python pipeline/features.py        # → scene_features.db (31,225행)
python pipeline/store_chroma.py    # → chroma/ (ChromaDB, emb_cache에서)
# 검증: ChromaDB ko_scenes count, scene_features.db 행수
pip install chromadb               # 미설치 시
```

## 3. 실행
```bash
cd <corpus_ko 작업폴더>
CHROMA_PATH=./chroma SCENES_DIR=./scenes GEN_MODEL=gpt-4o-mini OPENAI_API_KEY=... \
  python <repo>/docs/sessions/2026-06-13_corpus_ko_build/orchestration/e2e_pass5_local.py
```
- `GEN_MODEL=gpt-5-chat-latest` 로 GPT-5 생성도 가능(비용 14×).
- 출력: Pass6 통과율 · 평균 R · **Pass7 생성 vs 실명작 승률**.

## 4. 해석 기준 (사전등록)
- **Pass7 생성 << 실명작**(예: 생성 승 0~1/4)이 **정상**이다 — 아직 LLM-0 생성(공식·템플릿 보조)이라 거장 대본에 못 미치는 게 당연. **그 격차가 곧 학습 목표**(loop-C: 패널 선호쌍 → 생성기 LoRA/DPO).
- 생성이 실명작에 **대등(2/4 이상)** 이면 = 생성 품질이 이미 높거나 척도 변별 부족(추가 점검).
- **공식 R은 모델 품질 비교에 쓰지 말 것**(b 보고서: 구조 프록시, GPT-5 산문을 못 잼).

## 5. 본 모드 후속 (데이터 도착 시)
- Pass7 실명작 승률 + human_gt(작가) 1차 라운드 → loop-C 학습신호 가동.
- Critic 프롬프트 'WINNER:' 형식 강제(V755) 후 5축 critic으로 재판정.

재현 스크립트: `orchestration/e2e_pass5_local.py` (본 커밋 포함).
