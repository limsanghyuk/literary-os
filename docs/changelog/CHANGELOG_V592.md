# CHANGELOG V592 — SP-A.5 CorpusGovernance (v9.7.0)

## 릴리즈 정보
- **버전**: 9.7.0 (V592)
- **릴리즈일**: 2026-05-21
- **태그**: v9.7.0
- **커밋**: (자동)
- **기반**: v9.6.0 (V591 EquivalenceTester)

---

## 변경 사항

### 신규 파일

#### `literary_system/corpus/corpus_ingestor.py` (확장)
SP-A.5 — CorpusFallbackPipeline 및 3종 Ingestor 추가 (기존 CorpusIngestor 보존).
- `CorpusEntry` dataclass — entry_id / text / source_type / license / source_title / source_author / ingestor / word_count
- `CorpusFallbackOption` Enum — PUBLIC_DOMAIN / SYNTHETIC / ACADEMIC
- `PublicDomainIngestor` — 10종 한국 고전 문학 (공공 도메인)
- `SyntheticCorpusIngestor` — 기존 CorpusIngestor 래퍼 (CC-BY-4.0)
- `AcademicCorpusIngestor` — KOFICE/KOCCA 학술 협약 플레이스홀더
- `CorpusFallbackPipeline` — A→B→C 자동 폴백 + stats()

#### `literary_system/corpus/provenance_index.py` (신규, 192 lines)
SP-A.5 — 코퍼스 Provenance 추적 원장.
- `CorpusProvenanceRecord` — entry_id / source_type / license / sha256 / ingested_at / word_count
- `CorpusProvenanceIndex` — register() / register_batch() / lookup() / coverage() / has_license_violation()
- JSONL 영속화: to_jsonl() / from_jsonl()
- **ADR-053 핵심 조건**: 5천 신 Provenance 100% 추적 (coverage == 1.0) 검증

#### `literary_system/corpus/corpus_pii_filter.py` (신규, 175 lines)
SP-A.5 — 코퍼스 수집 전용 PII 필터링 (기존 PIIScrubber/PIIScrubberSP3/PIIScannerV2와 별도).
- `CorpusPiiMatch` — pattern_name / matched / start / end / placeholder
- `CorpusPiiFilter` — detect() / scrub() / is_clean() / filter_entries() / scan_summary()
- 4종 PII 패턴: 주민등록번호 / 전화번호 / 이메일 / 계좌번호
- strict 모드: True=항목 제거, False(기본)=플레이스홀더 대체
- LLM-0 준수: 순수 정규식 기반

#### `docs/adr/ADR-053.md` (신규)
CorpusGovernance 아키텍처 결정 기록.
- 3종 폴백 전략 (PUBLIC_DOMAIN → SYNTHETIC → ACADEMIC)
- Provenance 100% 추적 의무
- PII 제로 원칙

### 업데이트 파일

#### `literary_system/corpus/__init__.py`
SP-A.5 신규 클래스 exports 추가:
- CorpusEntry, CorpusFallbackOption, CorpusFallbackPipeline
- PublicDomainIngestor, SyntheticCorpusIngestor, AcademicCorpusIngestor
- CorpusProvenanceRecord, CorpusProvenanceIndex
- CorpusPiiMatch, CorpusPiiFilter

### 신규 테스트

#### `tests/unit/test_corpus_ingestor.py` (신규, TC01~TC20, 20/20 PASS)
- TC01~TC05: CorpusEntry 기본 생성 및 필드 검증
- TC06~TC10: 3종 Ingestor count / license 검증
- TC11~TC13: CorpusFallbackPipeline collect / stats / prefer 옵션
- TC14~TC17: CorpusProvenanceIndex register / coverage 검증
- TC18~TC20: JSONL 영속화 왕복 + 5천 신 Provenance 100% 추적 (ADR-053 핵심)

#### `tests/unit/test_pii_scrubber.py` (신규, TC01~TC15, 15/15 PASS)
- TC01~TC04: detect() 4종 PII 패턴
- TC05~TC09: scrub() 플레이스홀더 대체 검증
- TC10~TC12: is_clean() + filter_entries(strict=True)
- TC13~TC15: scan_summary() + CorpusPiiMatch.to_dict() + LLM-0 준수

---

## 수치

| 항목 | V591 (9.6.0) | V592 (9.7.0) |
|---|---|---|
| Gates | 49/49 | **49/49** (유지) |
| 신규 테스트 | — | **+35** |
| ADR | ADR-001~052 | **ADR-001~053** |
| CorpusGovernance | 없음 | **구현 완료** |
| 5천 신 Provenance | — | **100% 추적** |
| PII 필터 | — | **4종 패턴** |

---

## 아키텍처 결정

- **naming**: `CorpusProvenanceRecord` (기존 `ProvenanceRecord` from rag/retrieval_pipeline.py 충돌 회피)
- **naming**: `CorpusPiiFilter` (기존 PIIScrubber/PIIScrubberSP3/PIIScannerV2 충돌 회피)
- **LLM-0 원칙**: 외부 LLM 호출 0건 — 순수 정규식 + 해시 기반
- **JSONL 영속화**: CorpusProvenanceIndex 직렬화 (binary 없음, Git 친화)

---

## 보안/아키텍처 제약 (계속 유효)

- **LLM-0 원칙**: 외부 LLM 호출 0건
- **DEV_MODE** 기본값 항상 `"false"` (ADR-034)
- **Preflight 15단계**: 모든 버전 진입 전 필수
- **DuplicateZero (G37)**: 중복 클래스명 0건
