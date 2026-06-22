# 2026-06-21 work_id 명명 정규화 (권고 이행)

부분편입 조사에서 드러난 "명명 위생" 권고 이행. 데이터 손실 0, 비파괴(rename only).

## 정규화 39 work
- **제목유실 복원**: `1부`~`20부` → `신사의품격_01`~`신사의품격_20` (내용=신사의품격 확정).
- **공백 변형명**: `포도밭 그 사나이_NN`→`포도밭그사나이_NN`(16) · `이죽일놈의 사랑_11`→`이죽일놈의사랑_11` · `달콤한 인생`→`달콤한인생`.
- **회차표기**: `태양의후예 10회`→`태양의후예_10`.

## 정합 갱신 (전 계층)
- scenes/chunks/features 파일명 + 내부 work_id 필드 갱신.
- **emb_cache id 21 shard 갱신**(`old::`→`new::` 프리픽스). 
- **NKG 재빌드** 2,351 works·139,277 scene-node 반영.
- manifest 갱신, 역추적 로그 `_rename_log_20260621.json`.

## 마운트 특성 메모 (재현)
corpus_ko 마운트는 **rename(mv)는 허용, unlink(rm)은 차단**. → 파일 갱신은 in-place 후 `mv -f`(rename) 사용. `os.remove` 금지.

## 잔여
- **ChromaDB 집 재빌드** 필요(emb_cache id 변경 반영) — `store_chroma.py`, additive.
- 손상/누락 없음. 명명 일관성 확보로 제목기준 카운트·RAG·NextEp 페어링 개선.
