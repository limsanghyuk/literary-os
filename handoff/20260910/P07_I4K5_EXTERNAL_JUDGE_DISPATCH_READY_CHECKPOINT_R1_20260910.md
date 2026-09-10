# P07-I4K-5 External Judge Dispatch-Ready Checkpoint R1

Date: 2026-09-10

## Problem investigation
The I4K-5 research did not stop because of scientific failure, package corruption, OOM, or missing judge packets. Research Sync R15 physical audit is PASS and J01-J05 blind packets exist with preregistered hashes.

The execution boundary is capability/independence: the coordinator conversation cannot itself instantiate three genuinely separate fresh GPT conversations. Reusing the coordinator as three judges would violate the preregistered independence requirement and reproduce the project's previously identified same-model/same-session self-judge bias.

## Resolution completed
- Research Sync R15 physically sealed: material SHA `a21bdf7368541682e30828275e38d7a2018ed3c3d9c1da9eacbadf1af2f3cb8c`.
- CONTROL/A/B2 plus manifest/audit/closure persisted to Library.
- Primary J01/J02/J03 packets and response contract persisted individually and as a ZIP.
- Replacement J04/J05 packets persisted; replacement-only rule unchanged.
- Coordinator-private recovery persisted separately and MUST NOT be supplied to judges.
- J01/J02/J03 packet SHA256 values reverified against the pre-judge seal.
- Blind-leak scan: no secret-map SHA, Control/Treatment episode SHA, I4K4 +1.40 internal result, or PASS_TO_INDEPENDENT_GATE label appears in J01/J02/J03 packets.
- Runtime alive; OOM=0/OOM-kill=0. Page-cache hints dropped without modifying package bytes.

## External action required
Open three separate fresh GPT conversations outside the Literary OS Project. Attach exactly one packet to each conversation: J01, J02, J03. Do not share Hub context, coordinator map, internal scores, other judge responses, or coordinator-private recovery.

Each judge should follow the packet and return the contracted concise JSON/structured response including model/config and independence attestation. Do not ask the judge to reveal chain-of-thought.

## Resume after responses
Return the three exact responses to the coordinator conversation. Save/hash each response in receipt order. Do not open secret map until exactly three valid responses are sealed. Then unblind once and apply frozen H1-H4 without threshold changes.

Current state: `JUDGE_PACKETS_SEALED__RESPONSES_0__UNBLIND_0__NO_VERDICT`.
