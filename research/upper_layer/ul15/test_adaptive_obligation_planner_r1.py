import sys, pathlib, json, unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from adaptive_obligation_planner_r1 import *

class T(unittest.TestCase):
    def O(self,id,type,owners,urgency=.8,defer=.1,deps=(),conf=(),fun=("EF1",),delta=None):
        return Obligation(id,type,tuple(owners),{"v":0},delta or {"v":1},urgency,None,tuple(deps),tuple(conf),defer,("SRC",),tuple(fun))

    def test_no_fixed_quota_and_multi_owner(self):
        obs=[self.O("R1","RELATIONSHIP",["A","B"],conf=("I1",)),self.O("I1","INFORMATION",["B","C"],conf=("R1",)),self.O("E1","EVENT",["C"],.9),self.O("P1","PLANT_PAYOFF",["A"],.95)]
        p=AdaptiveObligationPlannerR1().plan(obs,{"id":"EF1"})
        ok,r,m=audit_plan(p)
        self.assertTrue(ok,r)
        self.assertIsNone(p["fixed_sequence_quota"])
        self.assertGreater(m["multi_obligation_sequence_share"],0)
        self.assertTrue(any(s["co_owners"] for s in p["sequence_transactions"]))

    def test_defer_is_not_fake_sequence_owner(self):
        obs=[self.O("A","EVENT",["X"],.95),self.O("B","THEMATIC_FUNCTION",["Y"],.1,defer=0)]
        p=AdaptiveObligationPlannerR1().plan(obs,{"id":"EF1"})
        self.assertTrue(any(d["disposition"]=="DEFER" for d in p["portfolio_disposition"]))
        self.assertFalse(any(str(s["primary_owner"]).startswith("DEFERRED") for s in p["sequence_transactions"]))

    def test_intervention_changes_architecture_hash(self):
        base=[self.O("R","RELATIONSHIP",["A","B"],.45,defer=.0),self.O("E","EVENT",["C"],.95)]
        p1=AdaptiveObligationPlannerR1().plan(base,{"id":"EF1"})
        changed=[self.O("R","RELATIONSHIP",["A","B"],.95,defer=.5),self.O("E","EVENT",["C"],.95)]
        p2=AdaptiveObligationPlannerR1().plan(changed,{"id":"EF1"})
        self.assertNotEqual(p1["architecture_sha256"],p2["architecture_sha256"])
        self.assertNotEqual([d["disposition"] for d in p1["portfolio_disposition"]],[d["disposition"] for d in p2["portfolio_disposition"]])

    def test_scene_contract_has_pre_post_and_downstream(self):
        p=AdaptiveObligationPlannerR1().plan([self.O("R","RELATIONSHIP",["A","B"],.95)],{"id":"EF1"})
        sc=p["scene_transactions"][0]
        for k in ("pre_state","post_state","downstream_consumer","necessity","merge_split_test","physical_action"):
            self.assertTrue(sc[k])

    def test_schema_validation_if_available(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema unavailable")
        obs=[self.O("R1","RELATIONSHIP",["A","B"],.95),self.O("I1","INFORMATION",["B"],.85)]
        p=AdaptiveObligationPlannerR1().plan(obs,{"id":"EF1"})
        with open(pathlib.Path(__file__).parent/"AdaptiveMultiObligationShowrunnerPlan.v1.schema.json", encoding="utf-8") as f:
            schema=json.load(f)
        jsonschema.validate(p,schema)

if __name__=='__main__': unittest.main()
