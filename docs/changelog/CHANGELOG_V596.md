# CHANGELOG — V596 (v10.1.0)

**릴리즈일**: 2026-05-21  
**버전**: v10.1.0  
**Phase**: B SP-B.1 — LoRA Fine-tuning Pipeline (첫 번째 버전)

---

## 신규 모듈

### literary_system/governance/

| 파일 | 클래스 | 설명 |
|------|--------|------|
| `provenance_ledger.py` | `LoRAProvenanceLedger`, `LedgerEntry`, `ProvenanceChainError` | sha256 체인 출처 원장. append-only, JSONL 영속화 |
| `dsr_handler.py` | `DSRHandler`, `DSRRequest`, `DSRStatus` | GDPR/PIPA DSR 핸들러. 30-day SLA 추적 |

### literary_system/finetune/ (추가)

| 파일 | 클래스 | 설명 |
|------|--------|------|
| `lora_dataset_builder.py` | `LoRADatasetBuilder`, `LoRASample` | CorpusEntry → Alpaca JSONL 변환. DSR 삭제 자동 제외 |
| `dataset_splitter.py` | `DatasetSplitter`, `LoRADatasetSplit` | 8:1:1 train/val/test 분할. seed=42 고정 |
| `dataset_registry.py` | `DatasetRegistry`, `LoRADatasetVersion` | sha256 검증 + DVC graceful degradation |

## ADR

- **ADR-056**: LoRA Dataset Format + ProvenanceLedger + DatasetRegistry + DSR 30-day SLA

## 테스트

- `tests/unit/test_v596_lora_governance.py`: 11 TC (TC-A1~A3, B1~B2, C1~C3, D1~D2, E1)
- 총 수집: **6,202 tests**
- Release Gate: **51/51 PASS**

## 버전

- pyproject.toml: `10.1.0`
- 태그: `v10.1.0`, `v10.1.0-V596`
