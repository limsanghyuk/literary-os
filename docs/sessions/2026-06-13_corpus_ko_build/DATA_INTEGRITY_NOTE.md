# ⚠️ 데이터 무결성 주의 — 집 복원 전 필독 (2026-06-13)

구글드라이브 업로드분(corpus_ko.zip 456M · chroma_export.tar.gz · corpus_ko_transfer · Scripts.zip) 무결성 검증 결과.

## ✅ 무손상 (핵심 자산, 대체 불가)
- `emb_cache/` 261샤드 (임베딩 51,996 — npy 정상)
- `scenes/` 31,225씬 · `chunks/` 51,996청크 · `txt/` 396 (JSONL 파싱 정상)
- **임베딩↔청크 정합 완벽**(고아 0)
- `experiments/`·`orchestration/`·집계 JSON·코드 정상
- Scripts.zip(원본 대본) 정상

## ★ 손상 — 집에서 재구축 필수 (2개 파생 파일)
| 파일 | 증상 | 원인 |
|---|---|---|
| `scene_features.db` | 0바이트(빈 파일) | FUSE 마운트 sqlite 쓰기 실패 |
| `chroma_export.tar.gz` | 잘림(unexpected EOF) | 백그라운드 tar 중간 종료 |

**둘 다 손실 아님 — 무손상 emb_cache+scenes로 재생성됨.**

## 집 복원 절차
1. corpus_ko.zip → `...\Documents\Claude\Projects\literary\` 해제. Scripts.zip → `C:\claude\Scripts\`.
2. 허브 코드: `git clone github.com/limsanghyuk/literary-os` (또는 pull).
3. **손상 2파일 재구축** (pipeline 스크립트 경로를 집 로컬로 수정 후):
   ```
   python features.py       # → scene_features.db (31,225행)
   python store_chroma.py   # → ChromaDB (51,996벡터, emb_cache에서)
   ```
   ※ 스크립트 내 `/sessions/upbeat-focused-bohr/...` 경로를 집 로컬 corpus_ko 경로로 치환.
4. 검증: `scene_features.db` 행수 31,225, ChromaDB scene 32,813+slide 19,183.

## 교훈(기록)
FUSE 마운트엔 sqlite/대용량 tar를 직접 쓰지 말 것 → 로컬디스크 빌드 후 복사. scene_features.db·chroma는 항상 emb_cache(원천)에서 재생성 가능하므로 emb_cache만 보존되면 무손실.
