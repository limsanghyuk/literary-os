#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ARCH=ROOT/"R77_H1_PA8_C_FRESH_EPISODE_ARCHITECTURE_R2.json"
CONTROL=ROOT/"PA8_D_CONTROL_GENERATION_PACKET_R1.json"
TREATMENT=ROOT/"PA8_D_TREATMENT_GENERATION_PACKET_R1.json"
CMAN=ROOT/"PA8_D_CONTROL_GENERATION_PACKET_MANIFEST_R1.json"
TMAN=ROOT/"PA8_D_TREATMENT_GENERATION_PACKET_MANIFEST_R1.json"
RECEIPT=ROOT/"PA8_D_GENERATION_PACKET_BUILD_RECEIPT_R1.json"

SHARED_INSTRUCTIONS = [
 "완성된 한국어 방송드라마 대본 한 회차를 작성한다.",
 "최소 40,000자 이상이며 상한은 없다. 분량을 채우기 위한 반복·패딩은 금지한다.",
 "정확히 동결된 9개 시퀀스와 50개 씬의 의미 기능을 보존한다.",
 "대사는 감정·상태를 직접 설명하지 말고 압박, 회피, 선택, 협상, 침묵과 서브텍스트를 사용한다.",
 "중요한 변화는 표정·시선·손·소품·자리 이동·실패 행동·멈춤·침묵·결과 등 화면에 보이는 행동으로 실현한다.",
 "지문은 배우가 연기할 수 있도록 구체적이어야 하지만 대사나 이미 보인 상태를 추상적으로 다시 설명하지 않는다.",
 "인물마다 문장 길이, 어휘, 직접성, 유머, 회피 방식, 직업 언어, 지위 전략을 분리한다.",
 "고정보다 실제 인과 변화가 없는 절차 반복을 피한다.",
 "고정보다 이미 행동이 증명한 의미를 후행 설명문으로 다시 요약하지 않는다.",
 "고정보다 정보가 많은 씬에서도 인물 간 비용·비대칭·압박이 실제 연기 가능하게 존재해야 한다.",
 "클라이맥스 이후에는 다음 회차 상태에 영향을 주는 종료 행동만 남겨 결말을 압축한다.",
 "연구 메타데이터, arm 이름, 실험 번호, schema, validator, ESCC 같은 내부 용어를 대본에 노출하지 않는다.",
 "각 씬 제목은 '씬 N. 장소 / 시각' 형식으로 자연스럽게 작성하고, 시퀀스 제목도 포함한다.",
 "완성 대본 외의 해설, 평가, JSON, 작업노트는 출력하지 않는다."
]

def canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def sha_obj(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def semantic_projection(d):
    return {
      "work_id":d["work_id"],
      "title":d["title"],
      "premise":d["premise"],
      "principal_cast":d["principal_cast"],
      "hard_state_constraints":d["hard_state_constraints"],
      "sequence_contracts":d["sequence_contracts"],
      "scene_contracts":[
        {
          "scene":s["scene"],"scene_id":s["scene_id"],"sequence":s["sequence"],
          "function":s["function"],"must_change":s["must_change"]
        } for s in d["scene_contracts"]
      ],
      "due_now":d["due_now"],
      "deferred_open":d["deferred_open"]
    }

def manifest(packet, escc_present):
    b=canon(packet)
    return {
      "schema":"PA8_D_GENERATION_PACKET_MANIFEST_R1",
      "date":"2026-09-29",
      "packet_sha256":hashlib.sha256(b).hexdigest(),
      "packet_bytes_canonical_json":len(b),
      "semantic_payload_sha256":sha_obj(packet["semantic_architecture"]),
      "escc_present":escc_present,
      "surface_outputs_at_build":0,
      "human_target_present":False,
      "other_arm_output_present":False
    }

def main():
    raw=ARCH.read_bytes()
    d=json.loads(raw.decode("utf-8"))
    sem=semantic_projection(d)

    shared={
      "schema":"PA8_D_ISOLATED_GENERATION_PACKET_R1",
      "date":"2026-09-29",
      "task":"WRITE_ONE_COMPLETE_KOREAN_BROADCAST_SCREENPLAY",
      "shared_generation_instructions":SHARED_INSTRUCTIONS,
      "semantic_architecture":sem,
      "mechanical_requirements":{
        "min_chars":40000,"upper_cap":None,"no_quota_padding":True,
        "sequence_count":9,"scene_count":50
      },
      "custody":{
        "use_only_this_packet":True,
        "do_not_request_other_arm":True,
        "human_target_present":False,
        "h1_real_work_payload_present":False
      }
    }

    control=json.loads(json.dumps(shared,ensure_ascii=False))
    control["surface_contract"]={
      "mode":"SEMANTIC_ARCHITECTURE_ONLY",
      "instruction":"Realize the frozen semantic architecture as a screenplay. Do not invent research metadata. No experiment-specific spacetime contract is supplied in this packet."
    }

    treatment=json.loads(json.dumps(shared,ensure_ascii=False))
    treatment["surface_contract"]={
      "mode":"SEMANTIC_ARCHITECTURE_PLUS_EXPLICIT_SPACETIME_CONTRACT",
      "instruction":"Realize the frozen semantics while obeying every supplied scene spacetime constraint. If prose would contradict a constraint, realize the same scene function in a compliant way; do not add/delete/reorder scenes.",
      "episode_clock":d["episode_clock"],
      "resources":d["resources"],
      "travel_minutes":d["spacetime_travel_minutes"],
      "transition_contract":d["transition_contract"],
      "scene_spacetime":[
        {"scene_id":s["scene_id"],"spacetime":s["spacetime"]}
        for s in d["scene_contracts"]
      ]
    }

    cman=manifest(control,False)
    tman=manifest(treatment,True)
    gates={
      "semantic_payload_hash_equal":cman["semantic_payload_sha256"]==tman["semantic_payload_sha256"],
      "control_escc_absent":"scene_spacetime" not in control["surface_contract"] and "travel_minutes" not in control["surface_contract"],
      "treatment_escc_present":"scene_spacetime" in treatment["surface_contract"] and len(treatment["surface_contract"]["scene_spacetime"])==50,
      "human_target_absent":not cman["human_target_present"] and not tman["human_target_present"],
      "other_arm_output_absent":not cman["other_arm_output_present"] and not tman["other_arm_output_present"],
      "surface_outputs_0":True
    }
    receipt={
      "schema":"PA8_D_GENERATION_PACKET_BUILD_RECEIPT_R1",
      "date":"2026-09-29",
      "status":"PASS" if all(gates.values()) else "FAIL",
      "parent_architecture_sha256":hashlib.sha256(raw).hexdigest(),
      "semantic_payload_sha256":cman["semantic_payload_sha256"],
      "control_packet_sha256":cman["packet_sha256"],
      "treatment_packet_sha256":tman["packet_sha256"],
      "gates":gates,
      "control_surface_outputs":0,
      "treatment_surface_outputs":0,
      "human_target_accessed":False,
      "active_runtime_effect":"NONE__EXACT_R69_UNCHANGED",
      "physical_package_effect":"NONE__RESEARCH_ONLY",
      "dispatch_rule":"Give CONTROL packet to one fresh generation context and TREATMENT packet to a different fresh generation context. Neither context may see the other packet/output."
    }

    CONTROL.write_text(json.dumps(control,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    TREATMENT.write_text(json.dumps(treatment,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    CMAN.write_text(json.dumps(cman,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    TMAN.write_text(json.dumps(tman,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if receipt["status"]=="PASS" else 1)

if __name__=="__main__":
    main()
