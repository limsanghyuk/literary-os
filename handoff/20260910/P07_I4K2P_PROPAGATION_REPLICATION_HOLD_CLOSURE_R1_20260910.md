# P07-I4K-2P Propagation Replication — HOLD Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-2P-SECOND-ORDER-PROPAGATION-REPLICATION`
Preregistration commit: `b6a21fd77522e42caf549d46f9346c19eb755429`
Final verdict: `HOLD__PROPAGATION_ARM_EXCEEDS_REPRESENTATION_BUDGET__NO_MASK__NO_SCORES__NO_HYPOTHESIS_VERDICT`

The preregistered Representation Parity Contract required 380–560 neutral characters per candidate and <=10% arm-level mean relative gap.

Observed exact generated outputs:
- STATE_ATTACHED_BASELINE: 16/16; neutral chars 448–521; mean 480.3125; SHA256 `af6683f75f9d73add80d55abd0dac6c8220bad1018ceebd8592329b5ddc31df5`.
- STATE_ATTACHED_PROPAGATION: 16/16; neutral chars 582–633; mean 599.1875; 16/16 exceed the 560 ceiling; SHA256 `4b8a726a8602bf5abaef861413d2b51ae259ee62e277e2ba6ba30f065b94aa6f`.
- Arm mean relative gap: `0.1983936581`, above frozen maximum `0.10`.

No candidate text was trimmed, rewritten, or regenerated. Because prescore integrity failed, secret masking, blind scoring, unblinding, and H1–H4 effect testing were never performed.

This is an integrity HOLD, not a scientific FAIL and not evidence against the Propagation Contract itself.

Next boundary: physical synchronization of this HOLD, then a separately preregistered fresh retry with prospective field-level realization budgets that prevent treatment-contract verbosity from becoming an arm confound. Old I4K-2P candidates may be used only as failure diagnosis, never as new experimental arms.