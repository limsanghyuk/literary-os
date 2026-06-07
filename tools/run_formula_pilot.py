import sys, json
sys.path.insert(0, "/tmp/v745x/repo")
from literary_system.physics.scene_feature_extractor import SceneFeature
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater

data=json.load(open("/tmp/pilot.json"))
scenes=data["scenes"]
feats=[]
for s in scenes:
    f=s["scene_features"]
    feats.append(SceneFeature(
        conflict_intensity=float(f["conflict_intensity"]),
        scene_energy_ratio=float(f["scene_energy_ratio"]),
        motif_residue_score=float(f["motif_residue_score"]),
        curiosity_gradient=float(f["curiosity_gradient"]),
        reader_uncertainty=float(f.get("curiosity_gradient",0.0)),  # proxy
    ))
print("주입 씬 수:", len(feats))
store=PhysicsCoefficientStore()
upd=PhysicsCoefficientUpdater(store)
print("초기 계수:", {k:round(v,4) for k,v in store.as_dict().items()})
print("파일럿 평균 신호: conflict=%.2f energy=%.2f motif=%.2f curiosity=%.2f"%(
    sum(f.conflict_intensity for f in feats)/len(feats),
    sum(f.scene_energy_ratio for f in feats)/len(feats),
    sum(f.motif_residue_score for f in feats)/len(feats),
    sum(f.curiosity_gradient for f in feats)/len(feats)))
for ep in range(1,6):
    out=upd.update_one_epoch(feats)
    if ep in (1,5):
        print(f"epoch{ep} 계수:", {k:round(v,4) for k,v in out.items()})
print("weight_sum:", round(store.weight_sum(),4))
print("=> 공식이 파일럿 실(L3) 신호로 계수를 갱신함 (gradient LR 0.01).")
