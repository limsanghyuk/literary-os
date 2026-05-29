# CHANGELOG V633

**버전**: v11.3.0  
**날짜**: 2026-05-26  
**기준선**: V632 (v11.2.0)  
**Phase**: Phase C SP-C.1 — Self-Learning Loop + Constitution v2.0  
**ADR**: ADR-075

---

## 요약

PatternLibraryV2 구현. LOSConstitutionV2 Bayesian Optimization이 발견한
패턴을 코사인 유사도 기반 압축(Compression)과 랭킹(Ranking)으로 관리.
LOSDB JSONL 영속화 지원.

추가로 V632 커밋 누락 파일(`test_v632_constitution_weight_tracker.py`) 복원.
실제 테스트 카운트 7,279 → 7,312로 정정.

---

## 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/constitution/pattern_library_v2.py` | PatternEntry + PatternLibraryV2 (압축+랭킹) |
| `docs/adr/ADR-075.md` | 설계 결정 문서 |
| `tests/unit/test_v633_pattern_library_v2.py` | TC-01~33, 33/33 PASS |
| `docs/changelog/CHANGELOG_V633.md` | 이 파일 |
| `manifests/MANIFEST_V633.md` | V633 산출물 목록 |

## 복원 파일

| 파일 | 설명 |
|------|------|
| `tests/unit/test_v632_constitution_weight_tracker.py` | V632 커밋 누락 → 복원 (+33 TC) |

## 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `literary_system/constitution/__init__.py` | PatternEntry, PatternLibraryV2 export 추가 |
| `pyproject.toml` | 11.2.0 → 11.3.0 |
| `tools/test_inventory.json` | 7,279 → 7,312 TC (source_hash 갱신) |

---

## V632 → V633 diff

| 지표 | V632 | V633 | 변화 |
|------|------|------|------|
| 버전 | 11.2.0 | 11.3.0 | +0.1.0 |
| Gates | 60/60 | 60/60 | 유지 |
| Tests | 7,279 | 7,312 | +33 |
| Unit PASS | 1,082 | 1,115 | +33 |
| ADR | ADR-099 | ADR-075 | 신규 |

---

## PatternLibraryV2 핵심 API

```python
lib = PatternLibraryV2(":memory:", similarity_threshold=0.92)
lib.add(PatternEntry(pattern_id=..., label="고조-절정-해소",
                     embedding=[1.0, 0.0], freq=10, entropy_weight=0.9))
ranked = lib.rank(top_k=5)           # rank_score 내림차순
before, after = lib.compress()       # 코사인 유사도 중복 제거
similar = lib.find_similar([1.0, 0.0], top_k=3)  # 유사 패턴 검색
```
