# P07-I4I Whole-Episode R1 — Closure & Physical Research Sync R1

Date: 2026-09-09

## 1. FINAL EXPERIMENT CLASSIFICATION
Experiment: `P07-I4I-WHOLE-EPISODE-PAIRED-RERENDER-R1`

Final verdict:
`CLOSED__PRIMARY_GATE_FAIL__POSITIVE_SCENE_LEVEL_SIGNAL__NO_PROMOTION`

Evidence class:
`DEVELOPMENT_PREFORMAL__VIRTUAL_PROVIDER_ANALOG__MASKED_SAME_AGENT`

This result is frozen. The preregistered whole-episode PASS threshold was Treatment-Control >= +0.30. Observed Treatment-Control was +0.2833333333333332, therefore the Primary Gate is FAIL. The threshold is not rounded or changed post-result.

## 2. FROZEN WHOLE-EPISODE RESULT
- frozen plan: 11 sequences / 56 scenes;
- Control: 35,036 Unicode characters, SHA256 `a48c53df49cd230b381a86795332905b0bf72d73f1374f253d46d58609ca551a`;
- Treatment: 35,108 Unicode characters, SHA256 `fda8a3e45f4b343245b0c988d77978ec4baec7af59f3d07e3f555cbbd9321ca8`;
- selector: ABSTAIN 32 / LOW 14 / STANDARD 10;
- Control episode mean: 8.075;
- Treatment episode mean: 8.358333333333333;
- Treatment-Control: +0.2833333333333332;
- 12/12 whole-episode axes nonloss;
- largest axis regression: 0.0;
- harmful intervention rate: 0.0;
- ABSTAIN byte identity: 1.0;
- critical failures: 0.

Secondary signals:
- LOW n=14: nonloss 1.0, mean scene-craft delta +0.4178571428571428, harmful 0.0;
- STANDARD n=10: nonloss 1.0, mean scene-craft delta +0.5850000000000002, harmful 0.0.

Blind-map SHA256: `7108578ae345390698750729fccf22c66e21056ebe602e1903ec7f7b5a438e82`.
Blind-score SHA256: `539b4b44bc2ab5db5aea77bb2979866ee363153812228b266786a1643137410f`.

## 3. INCIDENTS PRESERVED
Before Control sealing, an early size report incorrectly treated UTF-8 bytes as Unicode characters. The actual pre-seal Control was below the 35,000-character floor. Because this was detected before Control seal and before Selector profiling, the Control was repaired without changing the frozen 11/56 plan, then revalidated and sealed at 35,036 Unicode characters.

Before Control sealing, unauthorized/non-plan speaker labels and one missing planned participant were also detected and repaired. Final sealed Control passed scene-order, sequence-membership, authorized-speaker and participant-presence checks.

A blind-map attempt that exposed enough A/B file metadata to risk inference was discarded while scores were still 0. A new map was generated and only its hash was sealed before scoring. The final score was sealed before unblinding.

Because the same agent authored/profiled/treated and later performed masked evaluation, strict independent policy blindness is not claimed.

## 4. POST-EXPERIMENT REGRESSION
After closing I4I, the exact active I4H Recovery R3 parent nonhistorical suite was rerun:
`258/258 PASS`.

No active runtime code was changed by I4I.

## 5. AUTHORITY / CLAIM BOUNDARY
Active Development Engine remains:
`P07-I4H Recovery R3`.

Production remains `ENG:R47`.
DB Authority remains frozen `DB59` SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
Formal scored count remains 137; latest Formal authority R138; R140 remains 0/0/0.

I4I does not promote the active engine. It does not establish independent-human evidence or actual OpenAI Live evidence.

Semantic Alignment Virtual R1 remains a separate Live-pending non-active shadow candidate. DB64/9-Contract Candidate remains HOLD and is not adopted.

## 6. PHYSICAL RESEARCH-STATE SYNCHRONIZATION
I4I and the post-R3 session research results change research/authority evidence but not runtime or DB bytes. Therefore only three transport files were rebuilt append-only from the exact I4H Recovery R3 parents:

- CONTROL SHA256 `8f971865453a983da662114f962fee05e89d5e73065f734e62d65e472ecf0889`, bytes 108,647,898;
- Part A SHA256 `1b5f0a98932d5b480a7edca134148375c1fb15041c8f2f88bd43923f21ae1e13`, bytes 123,223,969;
- Part B2 SHA256 `aab1678e015f996f40bbbb25d2ae59030ce6cce1bd9ce6f9ee75f5c107fc901c`, bytes 255,327,694.

Reuse byte-identically from I4H Recovery R3:
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`;
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`;
- C2-A `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`;
- C2-B `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`;
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`;
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`.

Combined unchanged C2 SHA256 reverified:
`58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`.

Full logical 9-set material SHA256:
`9eadb1f41feb47fdea210a1d5215e00884fcb03889d31368c27265973514af16`.

Physical audit: PASS; changed ZIP CRC PASS; duplicate paths 0; unsafe paths 0; symlinks 0; encrypted entries 0; parent-member CRC/size mismatches 0.

## 7. CURRENT PHYSICAL PACKAGE AUTHORITY
Current developer-delivered physical package authority after this sync:
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R1__I4I_CLOSED_PRIMARY_FAIL`.

This is a research-state package supersession only. Active Development Engine remains P07-I4H Recovery R3.

## 8. NEXT RESEARCH BOUNDARY
Do not reinterpret I4I as PASS. Any follow-up that changes thresholds, selection policy, or whole-episode strategy requires a new preregistration.

Open paths remain separated:
1. Semantic Alignment candidate: genuine OpenAI Live confirmation when an API-capable environment is available;
2. DB64: data repair + A2 provenance/semantic separation, then requalification before DB59-vs-DB64 utility comparison;
3. I4I follow-up: knowledge-only dilution analysis may inspect why strong scene-level gains yielded +0.2833 at episode scale, but any new causal experiment must be preregistered independently.
