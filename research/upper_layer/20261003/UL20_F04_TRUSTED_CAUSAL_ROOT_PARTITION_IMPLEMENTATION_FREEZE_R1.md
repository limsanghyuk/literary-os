# UL20 — F04 Trusted Causal-Root Partition Implementation Freeze R1

Date: 2026-10-03  
Status: `IMPLEMENTED_SOURCE_FROZEN__FRESH_PRIMARY_NOT_CREATED`

## Parent / 부모
Physical Authority(물리 권위): **SYNC-R76**  
Active Runtime(활성 런타임): **UL18_F2_SUCCESSOR_RUNTIME_R1**  
Parent Runtime SHA256: `56254a8f52b19651638ab21ece2c35618e621e3aedc02d917efb6e22ca11db88`  
Parent adaptive source SHA256: `f2a22d1156f50152b8de1ae745d16e3189f6731758a83b8cc7dc2b37e8e8553b`

Preregistration:
`research/upper_layer/20261003/UL20_F04_TRUSTED_CAUSAL_ROOT_PARTITION_PREREG_R1.md`

## Frozen Treatment Source / 동결 처치 소스
Adaptive source SHA256:
`112a43d5609d2c35fb86c9f03f1494ba77f2da4118b02284c2db03334a6bf94a`

Canonical F04-only diff SHA256:
`b46f786af08748179dec36cccba790fc3e5ee934e283bc22630c2cc6faaed094`

Changed Python files:
- `literary_os_runtime/adaptive_showrunner_ul16.py` only

Added helper:
- `_trusted_causal_root_partition()`

Changed behavior:
- `_semantic_repetition_groups()` may partition an existing coarse R68 semantic signature only when caller-frozen source evidence validates.
- free-text `causal_root`, obligation ID, character ID, statement, and visible action never become partition keys.
- missing/invalid trusted evidence returns to the exact historical R68 bucket and diagnostic shape.

No change:
- scene generation;
- sequence allocation/weaving;
- F01 selector/parser;
- F06 scene necessity;
- F07 state carry;
- UL18 open-touch selection/resolution;
- DB / Provider / Production.

## Deterministic Adversarial Gate / 결정론 적대 관문
Frozen preimplementation suite:
`research/upper_layer/20261003/UL20_PREIMPLEMENTATION_ADVERSARIAL_SUITE_R1.json`

Result: **8/8 PASS**
- D01 same validated root repeat 3 -> FLAG
- D02 fake free-text labels / no evidence -> FLAG
- D03 same source identity / different labels -> FLAG
- D04 invalid evidence hash -> FLAG
- D05 three valid independent source records -> NO F04 FLAG
- D06 two same root + one independent -> NO >=3 partition flag
- D07 F04 does not overflag; F06 still finds redundant/mergeable scenes
- D08 irrelevant metadata sentinel -> semantic output unchanged

## Historical Regression / 역사 회귀
Exact frozen input SHA values:
- R66 fresh 12-case JSON: `9ba77865f1fd4f9f9ec91a23456686c026269f3ec5ed62c3490f2e43065bc5a7`
- R67 fresh 12-case JSON: `414d099308e3606acff8483c899eb4cd7f4b5783e2c98bc2b01ba20629d1cfcb`
- R68 fresh 16-case JSON: `fa57198f9f2dd142079da44179f36817b6bf4eee9b4f2d10d2b5eba33c7451e0`
- R69 fresh 16-case JSON: `09d547ede028aad0cd1b2b51c34cd6057dceb38463be1662684500de4219d3e7`

Results:
- R66 F01 exact frozen case projection: parent/candidate **bit-identical**, SHA `6433fcf2df4d1246f8e923bf2f4d310636da83a5804b4bd0342053d119697552`
- R67 F07 exact frozen dual-ledger replay: parent/candidate **bit-identical**, SHA `49aad5769b93ec70cb69f432e2ccb3ed7185a1b45f3cf6d429fd43508a11e8cd`
- R68 F04: **16/16 PASS**, parent/candidate diagnostic output **bit-identical**, SHA `e182559d1322ea918bde4539d355c3068dc9a2d5d89cfaa43df4f95f786bfdd3`
- R69 F06: **16/16 PASS**, parent/candidate output **bit-identical**, SHA `387e4107cf0adefcba0542b4b326be6c0fa7e214c444c2a0914584f9665c1e8a`
- UL18 four-state disposition/closure matrix: parent/candidate **bit-identical**, SHA `d3063a3889b3acf56cdd6cfd5881e546c43724c603b61e35fa343d191d190819`
- due=true / can_defer=false -> SELECTED_DUE / resolves once
- due=true / can_defer=true -> SELECTED_DUE / resolves once
- due=false / can_defer=true -> DEFERRED / unresolved
- due=false / can_defer=false -> SELECTED_OPEN_TOUCH / ADVANCE_KEEP_OPEN / unresolved / open debt retained

## Compile / Source Boundary / 컴파일·소스 경계
- Runtime Python compile: **45/45 PASS**
- changed Python files: **1**
- added/removed unrelated Python files: **0**

## Freeze Rule / 동결 규칙
This source is immutable for UL20 primary qualification.

Only after this commit may the fresh UL20 primary suite be created.
No rule, threshold, trusted-evidence contract, fallback behavior, or source code may be tuned after fresh primary inputs are sealed.

Authority effect: **NONE**. SYNC-R76 remains current physical authority.

Status token:
`UL20_SOURCE_FROZEN__F04_TRUSTED_ROOT_PARTITION_ONLY__ADVERSARIAL_8_OF_8_PASS__R66_R69_AND_UL18_REGRESSION_PASS__45_OF_45_COMPILE__FRESH_PRIMARY_NOT_CREATED`
