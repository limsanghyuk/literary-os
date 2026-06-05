# corpus_seed — 한국 서사 코퍼스 시드 (L0)

데이터 모델 v2(`docs/sessions/2026-06-05_data_model_v2_layered_blueprint.docx`)의 **L0 계층** 시드.
개발자 초기 실험 'V21 Master DB'를 `tools/corpus_migrate.py`로 v22 JSON 정규화한 결과.

## 내용
- `corpus_seed_L0.json` — **178편**(K-드라마 100 + 한국 영화 78), 인물 462·핵심오브제 180.
- 스키마: v22 (core_philosophy / lorebook / macro_causality / rendering / provenance).
- **저작권 안전**: 대사 verbatim 아님. 공개 작품의 '서사 DNA 분석'(source_kind=analysis, verbatim=false).

## 비고
- 원본 덤프 179편 중 1편은 닫는 태그 손상으로 파싱 제외 → 원본 수정 후 재마이그레이션으로 복구.
- 이것으로 '실데이터 0편'이 L0 수준에서 해소됨(검증 arm B/RAG의 기초 컨텍스트).

## 다음 (권고 순서)
1. ✅ L0 정규화(본 파일).
2. L1 승격: 관계 엣지·서브플롯 객체·인물 아크(전체 178편) — corpus/narrative_analyzer.py(LLM-1) 필요.
3. Gold 20~30편 선정(장르 균형) → L2(씬 분해)·L3(SceneFeature 정량 라벨) — LLM-1 분석기 1차 + 작가 검수.
4. L3 → scene_corpus_builder → physics_coefficient_updater(공식 계수 학습).

## 재생성
```
python tools/corpus_migrate.py   # XML 덤프 docx → corpus_seed_L0.json
```
