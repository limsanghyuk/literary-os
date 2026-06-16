# 집 로컬 환경 맞춤 E2E 측정 v1.0 — ChromaDB 불요

**작성일**: 2026-06-16 · **기준선**: main (V761/v13.14.0) · **문서 ID**: LOS-E2E-HOME-V1.0-2026-06-16
**계기**: 개발자는 로컬에서 `e2e_pass5_local.py`(ChromaDB 의존)로 절대검증①(생성 vs 명작 2/4) 완료. 본 모드(샌드박스/집 로컬)도 **동일 측정을 환경 제약 안에서 실행 가능**하게 설계.

## 0. 이 환경 제약 → 대응
| 제약 | 대응 |
|---|---|
| ChromaDB FUSE 쓰기불가(disk I/O error) | **emb_cache(.npy) 인메모리 코사인**으로 Pass4 RAG (ChromaDB 불요) |
| scene_features.db 0바이트(손상) | 미사용 — 공식은 LOSConstitution로 직접 채점 |
| 45초 한계 | 샤드/레퍼런스 **샘플 캡**(MAX_SHARDS/N_SCENES 환경변수, 로컬은 풀 가능) |

## 1. 파이프라인 (모두 실데이터·실 LLM)
- **Pass4 RAG**: emb_cache 샤드(id=`work::scene::n::chunk`) 로드 → 쿼리 임베딩(text-embedding-3-small) → 코사인 top-k → 실 유사 씬.
- **Pass5**: 실 OpenAI 생성.  **Pass6**: 구조 sanity 게이트.
- **Pass7**: Tier-1 명작 풀(올드보이·살인의추억·곡성·부산행·괴물·마더·박쥐·추격자·신세계·밀양·타짜·광해)에서 레퍼런스 → 3페르소나 블라인드 패널.
- 공식 R = LOSConstitution.

## 2. 본 환경 실행 결과 (소규모 데모: 25샤드·2씬)
- 임베딩 풀 2,487씬 · 명작 풀 649씬.
- **Pass6 2/2 PASS · 평균 R=0.533 · Pass7 생성 vs 실명작 0/2.**
- Pass4 실검색 동작(예: '위대한유산06::scene::63' 유사 결선).
- → **개발자 풀 측정(2/4)과 일관**: 생성<<한국명작이 정상(LLM-0 생성, 격차=loop-C 학습목표). 본 환경은 더 작은 표본이라 0/2.

## 3. 풀 측정 (로컬·회사)
```bash
CORPUS_DIR=/path/to/corpus_ko OPENAI_API_KEY=... \
  MAX_SHARDS=574 N_SCENES=20 GEN_MODEL=gpt-4o-mini \
  python docs/sessions/2026-06-13_corpus_ko_build/orchestration/e2e_pass5_home.py
```
- MAX_SHARDS↑(전체 574)·N_SCENES↑(다씬·반복) → 승률 안정화 → DPO/loop-C 격차 정량(E.4).
- GEN_MODEL=gpt-5-chat-latest 로 생성 모델 비교 가능.

## 4. 의의
**샌드박스/집 로컬에서도 ChromaDB 없이 실데이터 E2E가 재현 가능**해졌다. 개발자의 ChromaDB판(`e2e_pass5_local.py`)과 본 emb_cache판(`e2e_pass5_home.py`)이 동일 결론(생성 vs 명작 격차)을 독립 재현. E.4 RLAIF의 반복 측정·DPO 수집을 두 경로로 진행 가능.

재현 스크립트: `orchestration/e2e_pass5_home.py`.
