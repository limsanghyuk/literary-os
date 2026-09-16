from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple
import hashlib, json

SCHEMA_ID = "LiteraryOS.AdaptiveMultiObligationShowrunnerPlan.v1"
OBLIGATION_TYPES = {
    "EVENT", "CHARACTER", "RELATIONSHIP", "INFORMATION", "SOCIAL_GROUP",
    "WORLD_STATE", "PLANT_PAYOFF", "LONG_HORIZON_DEBT", "THEMATIC_FUNCTION"
}
DISPOSITIONS = {"SELECT", "DEFER", "DROP_WITH_REASON"}


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, tuple): return [_jsonable(x) for x in obj]
    if isinstance(obj, list): return [_jsonable(x) for x in obj]
    if isinstance(obj, dict): return {str(k):_jsonable(v) for k,v in obj.items()}
    return obj

def canonical_sha256(obj: Any) -> str:
    b = json.dumps(_jsonable(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class Obligation:
    id: str
    type: str
    owners: Tuple[str, ...]
    entry_state: Mapping[str, Any]
    desired_delta: Mapping[str, Any]
    urgency: float = 0.5
    horizon: int | None = None
    dependencies: Tuple[str, ...] = ()
    conflict_targets: Tuple[str, ...] = ()
    defer_cost: float = 0.0
    evidence_refs: Tuple[str, ...] = ()
    episode_function_refs: Tuple[str, ...] = ()

    def validate(self) -> List[str]:
        r=[]
        if not self.id: r.append("OBLIGATION_ID_MISSING")
        if self.type not in OBLIGATION_TYPES: r.append(f"OBLIGATION_TYPE_INVALID:{self.id}")
        if not self.owners: r.append(f"OBLIGATION_OWNER_MISSING:{self.id}")
        if not self.desired_delta: r.append(f"OBLIGATION_DELTA_MISSING:{self.id}")
        if not 0 <= float(self.urgency) <= 1: r.append(f"OBLIGATION_URGENCY_RANGE:{self.id}")
        return r


@dataclass
class PortfolioDisposition:
    obligation_id: str
    disposition: str
    reason: str
    cost: float = 0.0


@dataclass
class SequenceTransaction:
    id: str
    order: int
    primary_owner: str
    co_owners: List[str]
    obligation_ids: List[str]
    prerequisites: List[str]
    transaction: str
    state_deltas: Dict[str, Any]
    turn: str
    exit_pressure: str
    downstream_consumers: List[str] = field(default_factory=list)


@dataclass
class SceneTransaction:
    id: str
    sequence_id: str
    obligation_ids: List[str]
    actors: List[str]
    goal: str
    opposition: str
    physical_action: str
    information_change: str
    relationship_transaction: str
    pre_state: Dict[str, Any]
    post_state: Dict[str, Any]
    downstream_consumer: str
    necessity: str
    merge_split_test: str
    subtext_constraint: str


class AdaptiveObligationPlannerR1:
    """Reference planning implementation for research qualification.

    It has no fixed sequence/scene/axis quota. It consumes a typed obligation
    portfolio, selects/defer obligations, builds variable multi-obligation sequence
    transactions, and emits scene contracts only from explicit transactions.
    It does not render dialogue/screenplay surface.
    """
    def __init__(self, max_sequence_obligations: int = 3):
        if max_sequence_obligations < 1:
            raise ValueError("max_sequence_obligations must be >=1")
        self.max_sequence_obligations=max_sequence_obligations

    @staticmethod
    def _score(o: Obligation) -> float:
        deadline_pressure = 0.0 if o.horizon is None else 1.0 / max(1, o.horizon)
        return float(o.urgency) + float(o.defer_cost) + deadline_pressure

    @staticmethod
    def _compatible(a: Obligation, b: Obligation) -> bool:
        owner_overlap = bool(set(a.owners) & set(b.owners))
        conflict_link = b.id in a.conflict_targets or a.id in b.conflict_targets
        dependency_link = b.id in a.dependencies or a.id in b.dependencies
        function_overlap = bool(set(a.episode_function_refs) & set(b.episode_function_refs))
        return owner_overlap or conflict_link or dependency_link or function_overlap

    def select(self, obligations: Sequence[Obligation], episode_capacity_hint: float | None = None):
        reasons=[]
        by={o.id:o for o in obligations}
        for o in obligations: reasons += o.validate()
        if len(by) != len(obligations): reasons.append("DUPLICATE_OBLIGATION_ID")
        if reasons: raise ValueError(";".join(reasons))

        threshold = 0.70 if episode_capacity_hint is None else max(0.35, min(0.9, 1.0-float(episode_capacity_hint)*0.25))
        selected=[]; disp=[]
        for o in sorted(obligations, key=lambda x:(-self._score(x), x.id)):
            critical = self._score(o) >= threshold or (o.horizon is not None and o.horizon <= 1)
            if critical:
                selected.append(o)
                disp.append(PortfolioDisposition(o.id,"SELECT","episode-pressure/causal-readiness",o.defer_cost))
            else:
                disp.append(PortfolioDisposition(o.id,"DEFER","lower-current-pressure",o.defer_cost))
        if not selected and obligations:
            o=max(obligations,key=self._score); selected=[o]
            for d in disp:
                if d.obligation_id==o.id:
                    d.disposition="SELECT"; d.reason="minimum-narrative-motion"
        return selected, disp

    def build_sequences(self, selected: Sequence[Obligation]) -> List[SequenceTransaction]:
        pending=list(sorted(selected,key=lambda x:(-self._score(x),x.id)))
        used:Set[str]=set(); groups=[]
        while pending:
            selected_ids={x.id for x in selected}
            seed=next((o for o in pending if all(d in used or d not in selected_ids for d in o.dependencies)), pending[0])
            group=[seed]
            for cand in list(pending):
                if cand.id==seed.id or len(group)>=self.max_sequence_obligations: continue
                if self._compatible(seed,cand) or any(self._compatible(g,cand) for g in group):
                    group.append(cand)
            for g in group:
                if g in pending: pending.remove(g)
                used.add(g.id)
            groups.append(group)

        seqs=[]
        for i,group in enumerate(groups,1):
            owner_counts={}
            for o in group:
                for own in o.owners: owner_counts[own]=owner_counts.get(own,0)+1
            primary=sorted(owner_counts,key=lambda k:(-owner_counts[k],k))[0]
            co=sorted(k for k in owner_counts if k!=primary)
            seqs.append(SequenceTransaction(
                id=f"SQ{i:02d}", order=i, primary_owner=primary, co_owners=co,
                obligation_ids=[o.id for o in group],
                prerequisites=sorted({d for o in group for d in o.dependencies}),
                transaction="INTERLOCK:"+"+".join(o.type for o in group),
                state_deltas={o.id:dict(o.desired_delta) for o in group},
                turn="state-or-information-turn-required",
                exit_pressure="unresolved consequence transferred forward",
            ))
        for a,b in zip(seqs,seqs[1:]): a.downstream_consumers.append(b.id)
        return seqs

    def build_scene_contracts(self, seqs: Sequence[SequenceTransaction], by_obligation: Mapping[str,Obligation]) -> List[SceneTransaction]:
        scenes=[]
        for s in seqs:
            actors=sorted({x for oid in s.obligation_ids for x in by_obligation[oid].owners})
            pre={oid:dict(by_obligation[oid].entry_state) for oid in s.obligation_ids}
            post={oid:dict(by_obligation[oid].desired_delta) for oid in s.obligation_ids}
            scenes.append(SceneTransaction(
                id=f"{s.id}_SC01", sequence_id=s.id,
                obligation_ids=list(s.obligation_ids), actors=actors,
                goal="advance at least one selected obligation through action",
                opposition="another owner, constraint, or incompatible state blocks the goal",
                physical_action="must be concretized by semantic planner; exposition-only is forbidden",
                information_change="access/belief/secret/public-state must be explicit if changed",
                relationship_transaction="status/power/trust/debt delta must be explicit if changed",
                pre_state=pre, post_state=post,
                downstream_consumer=(s.downstream_consumers[0] if s.downstream_consumers else "EPISODE_EXIT_STATE"),
                necessity="removal must break a selected obligation, causal dependency, or episode function",
                merge_split_test="merge if same transaction can carry deltas without loss; split only for distinct dramatic transaction",
                subtext_constraint="dialogue may not restate internal state or plot explanation already available in direction/action",
            ))
        return scenes

    def plan(self, obligations: Sequence[Obligation], episode_function: Mapping[str,Any], episode_capacity_hint: float|None=None) -> Dict[str,Any]:
        selected,disp=self.select(obligations,episode_capacity_hint)
        seqs=self.build_sequences(selected)
        by={o.id:o for o in obligations}
        scenes=self.build_scene_contracts(seqs,by)
        out={
            "schema":SCHEMA_ID,
            "episode_function":dict(episode_function),
            "obligation_portfolio":[_jsonable(asdict(o)) for o in obligations],
            "portfolio_disposition":[asdict(d) for d in disp],
            "sequence_transactions":[asdict(s) for s in seqs],
            "scene_transactions":[asdict(s) for s in scenes],
            "fixed_sequence_quota":None,
            "fixed_scene_quota":None,
        }
        out["architecture_sha256"]=canonical_sha256(out)
        return out


def audit_plan(plan: Mapping[str,Any]) -> Tuple[bool,List[str],Dict[str,Any]]:
    r=[]
    if plan.get("schema") != SCHEMA_ID: r.append("SCHEMA_ID_MISMATCH")
    if plan.get("fixed_sequence_quota") is not None: r.append("FIXED_SEQUENCE_QUOTA_FORBIDDEN")
    if plan.get("fixed_scene_quota") is not None: r.append("FIXED_SCENE_QUOTA_FORBIDDEN")
    seqs=plan.get("sequence_transactions") or []
    scenes=plan.get("scene_transactions") or []
    disp=plan.get("portfolio_disposition") or []
    if any(str(d.get("disposition")) not in DISPOSITIONS for d in disp): r.append("INVALID_DISPOSITION")
    if any(str(s.get("primary_owner","")).startswith("DEFERRED") for s in seqs): r.append("DEFERRED_AS_SEQUENCE_OWNER_FORBIDDEN")
    if any(not s.get("obligation_ids") or not s.get("state_deltas") for s in seqs): r.append("EMPTY_SEQUENCE_TRANSACTION")
    required_scene=("goal","opposition","physical_action","pre_state","post_state","downstream_consumer","necessity","merge_split_test")
    if any(any(not sc.get(k) for k in required_scene) for sc in scenes): r.append("SCENE_TRANSACTION_INCOMPLETE")
    counts={}
    for s in seqs:
        p=s.get("primary_owner"); counts[p]=counts.get(p,0)+1
    dominance=(max(counts.values())/len(seqs)) if seqs and counts else 0.0
    multi=sum(len(s.get("obligation_ids") or [])>=2 for s in seqs)/(len(seqs) or 1)
    metrics={"sequence_count":len(seqs),"scene_contract_count":len(scenes),"primary_owner_dominance":dominance,"multi_obligation_sequence_share":multi}
    return not r,r,metrics
