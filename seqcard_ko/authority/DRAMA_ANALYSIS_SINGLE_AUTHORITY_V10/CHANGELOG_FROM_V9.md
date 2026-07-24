# V9 → V10 변경 이력

V10은 〈질투의 화신〉 24부작 전 시즌 분석·Stage04·DB79 신규 편입에서 검증된 규칙을 편입한다.

## 추가된 강제 규칙

1. 신규 작품 선정 시 완전 원본 후보 검증과 제외 후보 원장
2. HWP/PDF 추출기의 원본 SHA·추출 SHA·회귀 표본 검사
3. 삭제 장면, 삽입 장면, 번호 없는 장면, 누락 번호 처리
4. `source_label`과 canonical `scene_no` 분리
5. RelationshipArc 복합 가상 인물 금지와 alias registry
6. Sequence 밀도 하한을 기계 분절로 맞추는 행위 금지
7. Stage04 승격 4문항과 최종회 집결 과승격 금지
8. callback·subplot_counterpoint·plant_payoff 유형 교정
9. UTF-8 filename, Windows path length, traversal, actual extraction 검사
10. 신규 작품 DB 추가와 기존 작품 전량 교체 절차 분리
11. 진행 보고와 실제 영속 저장 상태 불일치 금지
12. 수호천사·눈이 부시게·질투의 화신을 3종 acceptance suite로 지정

Stage01–04 exact schema는 V9와 호환된다.
