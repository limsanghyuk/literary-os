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

---

## 🔄 갱신 (2026-06-15) — 인코딩 결함 교정 + 전면 재처리

**중대**: 위 "무손상" 기준은 **인코딩 교정 전(stale)**. 2026-06-15 NER 폴백이 깨진 이름(ȯⱸ)을 반환 → 추적 결과 **소스 UTF-16을 utf-8로 읽어 112편(코퍼스 25%)이 모지바케**였음. `fix_encoding.py`(utf-16→cp949→utf-8 한글비율 폴백, idempotent)로 일괄 교정 후 **tri-store 전면 재처리**.

### 현재 권위 상태 (교정본)
- 코퍼스 **455편 / 62,514 벡터**(emb_cache 313샤드). txt 0-깨짐(`fix_encoding.py` 재실행 시 fixed=0/skipped=455 확인).
- 청크 62,514 = 임베딩 62,514 = ChromaDB 62,514(scene 38,450 + slide 24,064). 고아 0.
- features 36,291행 / 455작품. 상세 입증: `experiments/INTEGRITY_PROOF_2026-06-15.md`.

### 집 복원 — 갱신된 주의
1. **Drive `corpus_ko.zip`(456M)은 교정 전 버전 → 재업로드 필요**(또는 교정된 워크스페이스 폴더 동기화). 그대로 복원하면 모지바케 112편이 되살아남.
2. `scene_features.db`·ChromaDB는 여전히 FUSE 직접쓰기 불가 → **교정된 emb_cache로 로컬 재빌드**: `store_chroma.py` + `features.py`(둘 다 CACHE=emb_cache로 갱신됨).
3. `연애의목적.hwp`(HWP5) 1편은 추출 실패(txt 0바이트, 455 카운트 밖) — 재추출 과제.
