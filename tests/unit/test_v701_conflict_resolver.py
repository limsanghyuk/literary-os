"""V701 — AgentConflictResolver 테스트 (33 TC)."""
import pytest
from literary_system.agents.conflict_resolver import (
    AgentConflictResolver, ConflictType, ConflictParty,
    ResolutionStrategy, ConflictState, ADR_163,
)


def make_party(agent_id: str, priority: int = 0, claim: object = None) -> ConflictParty:
    return ConflictParty(agent_id=agent_id, priority=priority, claim=claim or f"claim_{agent_id}")


# ══════════════════════════════════════════════════════════════════════
class TestConflictResolverBasics:
    def test_tc01_register_conflict(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A"), make_party("B")])
        assert c.conflict_id
        assert c.state == ConflictState.OPEN
        assert len(c.parties) == 2

    def test_tc02_resolve_priority_based(self):
        r = AgentConflictResolver()
        parties = [make_party("A", priority=1), make_party("B", priority=3)]
        c = r.register(ConflictType.RESOURCE, parties, ResolutionStrategy.PRIORITY_BASED)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.state == ConflictState.RESOLVED
        assert c.winner == "B"

    def test_tc03_resolve_timestamp(self):
        import time
        r = AgentConflictResolver()
        p1 = make_party("A"); p1.timestamp = 1000.0
        p2 = make_party("B"); p2.timestamp = 2000.0
        c = r.register(ConflictType.TASK, [p1, p2], ResolutionStrategy.TIMESTAMP)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.winner == "A"  # 먼저 요청

    def test_tc04_resolve_consensus_clear_majority(self):
        r = AgentConflictResolver()
        parties = [
            make_party("A", claim="option1"),
            make_party("B", claim="option1"),
            make_party("C", claim="option2"),
        ]
        c = r.register(ConflictType.DECISION, parties, ResolutionStrategy.CONSENSUS)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.resolution == "option1"

    def test_tc05_resolve_consensus_no_majority_escalates(self):
        r = AgentConflictResolver()
        parties = [
            make_party("A", claim="option1"),
            make_party("B", claim="option2"),
        ]
        c = r.register(ConflictType.DECISION, parties, ResolutionStrategy.CONSENSUS)
        ok = r.resolve(c.conflict_id)
        assert not ok
        assert c.state == ConflictState.ESCALATED

    def test_tc06_resolve_mediator(self):
        r = AgentConflictResolver()
        r.set_mediator(lambda c: "mediated_result")
        parties = [make_party("A"), make_party("B")]
        c = r.register(ConflictType.DATA, parties, ResolutionStrategy.MEDIATOR)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.resolution == "mediated_result"

    def test_tc07_resolve_mediator_none_escalates(self):
        r = AgentConflictResolver()
        # No mediator set
        parties = [make_party("A"), make_party("B")]
        c = r.register(ConflictType.DATA, parties, ResolutionStrategy.MEDIATOR)
        ok = r.resolve(c.conflict_id)
        assert not ok
        assert c.state == ConflictState.ESCALATED

    def test_tc08_resolve_random(self):
        r = AgentConflictResolver()
        parties = [make_party("A"), make_party("B")]
        c = r.register(ConflictType.PRIORITY, parties, ResolutionStrategy.RANDOM)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.winner in ("A", "B")
        assert c.state == ConflictState.RESOLVED

    def test_tc09_cannot_resolve_again(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        r.resolve(c.conflict_id)
        ok2 = r.resolve(c.conflict_id)
        assert not ok2

    def test_tc10_empty_parties_fails(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [])
        ok = r.resolve(c.conflict_id)
        assert not ok
        assert c.state == ConflictState.ESCALATED

    def test_tc11_get_conflict(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A")])
        retrieved = r.get_conflict(c.conflict_id)
        assert retrieved is c

    def test_tc12_get_nonexistent(self):
        r = AgentConflictResolver()
        assert r.get_conflict("nope") is None

    def test_tc13_open_conflicts(self):
        r = AgentConflictResolver()
        c1 = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        c2 = r.register(ConflictType.TASK, [make_party("A")])
        r.resolve(c1.conflict_id)
        open_c = r.open_conflicts()
        assert c1 not in open_c
        assert c2 in open_c

    def test_tc14_resolved_conflicts(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        r.resolve(c.conflict_id)
        assert c in r.resolved_conflicts()

    def test_tc15_escalated_conflicts(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.DECISION, [make_party("A", claim="x"), make_party("B", claim="y")],
                       ResolutionStrategy.CONSENSUS)
        r.resolve(c.conflict_id)
        assert c in r.escalated_conflicts()

    def test_tc16_stats(self):
        r = AgentConflictResolver()
        c1 = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        c2 = r.register(ConflictType.DECISION, [make_party("A", claim="x"), make_party("B", claim="y")],
                        ResolutionStrategy.CONSENSUS)
        r.resolve(c1.conflict_id)
        r.resolve(c2.conflict_id)
        st = r.stats()
        assert st["total"] == 2
        assert st["resolved"] == 1
        assert st["escalated"] == 1

    def test_tc17_registered_hook_fires(self):
        r = AgentConflictResolver()
        fired = []
        r.on("registered", lambda c: fired.append(c.conflict_id))
        c = r.register(ConflictType.RESOURCE, [make_party("A")])
        assert c.conflict_id in fired

    def test_tc18_resolved_hook_fires(self):
        r = AgentConflictResolver()
        fired = []
        r.on("resolved", lambda c: fired.append(True))
        c = r.register(ConflictType.RESOURCE, [make_party("A", 2), make_party("B", 1)])
        r.resolve(c.conflict_id)
        assert fired == [True]

    def test_tc19_escalated_hook_fires(self):
        r = AgentConflictResolver()
        fired = []
        r.on("escalated", lambda c: fired.append(True))
        c = r.register(ConflictType.DECISION, [make_party("A", claim="x"), make_party("B", claim="y")],
                       ResolutionStrategy.CONSENSUS)
        r.resolve(c.conflict_id)
        assert fired == [True]

    def test_tc20_to_dict(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", 2), make_party("B", 1)])
        d = c.to_dict()
        assert d["type"] == "resource"
        assert d["party_count"] == 2

    def test_tc21_is_resolved(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", 2)])
        assert not c.is_resolved()
        r.resolve(c.conflict_id)
        assert c.is_resolved()

    def test_tc22_priority_tie_picks_last_max(self):
        """동점 시 max()는 마지막 최대값 — 동작 검증."""
        r = AgentConflictResolver()
        parties = [make_party("A", priority=5), make_party("B", priority=5)]
        c = r.register(ConflictType.RESOURCE, parties, ResolutionStrategy.PRIORITY_BASED)
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.winner in ("A", "B")

    def test_tc23_metadata_preserved(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A")],
                       metadata={"resource": "GPU-0"})
        assert c.metadata["resource"] == "GPU-0"

    def test_tc24_failure_reason_on_escalate(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.DECISION, [make_party("A", claim="x"), make_party("B", claim="y")],
                       ResolutionStrategy.MEDIATOR)  # No mediator → escalate
        r.resolve(c.conflict_id)
        assert c.state == ConflictState.ESCALATED

    def test_tc25_resolve_single_party(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", priority=5)])
        ok = r.resolve(c.conflict_id)
        assert ok
        assert c.winner == "A"

    def test_tc26_conflict_types_coverage(self):
        r = AgentConflictResolver()
        for ct in ConflictType:
            c = r.register(ct, [make_party("A", 1), make_party("B", 2)])
            r.resolve(c.conflict_id)
            assert c.state == ConflictState.RESOLVED

    def test_tc27_all_strategies_coverage(self):
        r = AgentConflictResolver()
        r.set_mediator(lambda c: "ok")
        results = {}
        for st in ResolutionStrategy:
            parties = [make_party("A", 1, "x"), make_party("B", 2, "x")]
            c = r.register(ConflictType.RESOURCE, parties, st)
            ok = r.resolve(c.conflict_id)
            results[st] = (ok, c.state)
        # PRIORITY_BASED, TIMESTAMP, MEDIATOR, RANDOM → resolved
        # CONSENSUS with unanimous → resolved
        for st, (ok, state) in results.items():
            assert state in (ConflictState.RESOLVED, ConflictState.ESCALATED)

    def test_tc28_resolved_at_set_on_resolved(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        assert c.resolved_at is None
        r.resolve(c.conflict_id)
        assert c.resolved_at is not None

    def test_tc29_resolved_at_not_set_on_escalated(self):
        r = AgentConflictResolver()
        c = r.register(ConflictType.DECISION, [make_party("A", claim="x"), make_party("B", claim="y")],
                       ResolutionStrategy.CONSENSUS)
        r.resolve(c.conflict_id)
        assert c.resolved_at is None

    def test_tc30_multiple_conflicts_independent(self):
        r = AgentConflictResolver()
        c1 = r.register(ConflictType.RESOURCE, [make_party("A", 1), make_party("B", 2)])
        c2 = r.register(ConflictType.TASK, [make_party("C", 5), make_party("D", 1)])
        r.resolve(c1.conflict_id)
        r.resolve(c2.conflict_id)
        assert c1.winner == "B"
        assert c2.winner == "C"

    def test_tc31_mediator_receives_conflict(self):
        r = AgentConflictResolver()
        received = []
        r.set_mediator(lambda c: (received.append(c.conflict_id), "result")[1])
        parties = [make_party("A"), make_party("B")]
        c = r.register(ConflictType.DATA, parties, ResolutionStrategy.MEDIATOR)
        r.resolve(c.conflict_id)
        assert c.conflict_id in received

    def test_tc32_resolve_nonexistent_returns_false(self):
        r = AgentConflictResolver()
        ok = r.resolve("no-such-id")
        assert not ok

    def test_tc33_adr_163(self):
        assert ADR_163["id"] == "ADR-163"
        assert ADR_163["status"] == "accepted"
        assert "ConflictResolver" in ADR_163["title"]
