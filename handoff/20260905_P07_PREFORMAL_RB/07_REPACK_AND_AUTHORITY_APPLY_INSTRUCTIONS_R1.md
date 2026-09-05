# Repack & Authority Apply Instructions(재봉인·권위 적용 지침) R1

## 목표
이번 세션의 내용을 5파트 8패키지 체계에 반영한다.

## 최신 기준 계보
- CONTROL: R27 계보에서 다음 revision 생성
- PART-A: R26 계보에서 다음 revision 생성
- PART-B1: R10 바이트 불변
- PART-B2: R27 계보에서 다음 revision 생성
- PART-C1: R10 ENG:R47 바이트 불변
- PART-C2: R26 후보엔진 계보에서 다음 revision 생성
- PART-D1: R10 DB59 바이트 불변
- PART-D2: R10 DB59 Learning 바이트 불변

## 변경 4패키지에 공통 편입할 디렉터리
`P07_SESSION_HANDOFF_R21_20260905/`
그 안에 이 GitHub handoff 디렉터리의 00~06 문서를 모두 넣는다.

## 패키지별 추가 편입
### CONTROL
- `CURRENT_AUTHORITY_POINTER_R21.json`
- `SESSION_END_STATUS_R21.md`
- `EIGHT_PACKAGE_APPLY_MATRIX_R21.md`
- `BACKEND_INCIDENT_R1.md`

### PART-A
- R5~R8 결과 요약/주장경계
- P07-PRE-09 E0~E9 단계 요약
- R-B 사전등록 R1
- Formal count delta 0 명시

### PART-B2
- Research→Engine Propagation Doctrine(연구→엔진 전파 교리)
- Ensemble/Ecology/Event Ownership 전체 재감사
- P07 readiness correction(준비도 판정 교정)
- R-B~R-G 향후 연구순서

### PART-C2
- 최신 Development Overlay(개발 오버레이) 소스가 정상 접근될 경우 그대로 포함
- 최신 소스 접근 불가 시 문서만으로 엔진을 새로 추정 생성하지 말고 `SOURCE_SNAPSHOT_RECOVERY_REQUIRED`로 HOLD
- R-B 구현 요구사항 및 Consumer Fidelity Gate 명세

## 불변 4패키지 규칙
B1/C1/D1/D2를 재압축하여 새 SHA를 만들 필요가 없다. 기존 파일을 그대로 전달하고 새 CONTROL이 이들의 기존 해시를 참조한다.

## Fresh Validation(새 검증)
변경 4 ZIP 각각:
- CRC error = 0
- 모든 JSON parse = PASS
- 필수 handoff 파일 존재
- Formal scored count = 137
- R140 formal attempts/outputs/scores = 0/0/0
- ENG:R47 unchanged
- DB59 hash unchanged

전체 8패키지 Handoff Audit(인계 감사): `errors=[]`만 허용.

## 권위 서열
1. 새 CONTROL
2. 새 PART-A/B2/C2
3. 불변 B1/C1/D1/D2
4. 이 GitHub handoff branch는 **로컬 ZIP 재봉인 완료 전 임시 Source of Truth(원천 권위)**로 사용
5. ZIP 재봉인과 Fresh Validation이 끝나면 새 CONTROL이 최종 물리 권위가 되고 branch는 Provenance(출처계보) 보조증거로 남김.