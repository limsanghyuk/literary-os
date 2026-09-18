#!/usr/bin/env node
/**
 * Build the frozen SYNC-R58 P06 Provider request from the sealed J02 blind packet.
 *
 * Infrastructure only:
 * NO_ENGINE_CODE_CHANGE__PHYSICAL_AUTHORITY_UNCHANGED
 *
 * Frozen source after legal mapping reveal:
 *   J02 P06 Candidate arm = A
 *   J02 packet ZIP SHA256 =
 *     4a4a4100c4dbe85bbe9689606c5f11781c4b790ddb673946db01c4787aca9066
 *
 * Requires the system 'unzip' command. It fails closed if P06 or arm A cannot
 * be located unambiguously in JSON content.
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";

const EXPECTED_PACKET_SHA =
  "4a4a4100c4dbe85bbe9689606c5f11781c4b790ddb673946db01c4787aca9066";
const FROZEN_PAIR = "P06";
const FROZEN_ARM = "A";

function sha256(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function die(message, code = 2) {
  process.stderr.write(message + "\n");
  process.exit(code);
}

function parseArgs(argv) {
  const out = { maxOutputTokens: 40000 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--packet") out.packet = argv[++i];
    else if (a === "--outdir") out.outdir = argv[++i];
    else if (a === "--model") out.model = argv[++i];
    else if (a === "--max-output-tokens") {
      out.maxOutputTokens = Number(argv[++i]);
    } else if (a === "--help") {
      process.stdout.write(
        "Usage: node prepare_sync_r58_p06_provider_request_r1.mjs " +
        "--packet J02_SYNC_R58_ARCHITECTURE_ONLY_BLIND_PACKET_R1.zip " +
        "--outdir DIR --model MODEL [--max-output-tokens N]\n"
      );
      process.exit(0);
    } else {
      die("Unknown argument: " + a);
    }
  }
  if (!out.packet) die("--packet is required");
  if (!out.outdir) die("--outdir is required");
  if (!out.model) die("--model is required");
  if (!Number.isInteger(out.maxOutputTokens) || out.maxOutputTokens < 35000) {
    die("--max-output-tokens must be an integer >= 35000");
  }
  return out;
}

function listZipEntries(zipPath) {
  try {
    return execFileSync("unzip", ["-Z1", zipPath], {
      encoding: "utf8",
      maxBuffer: 16 * 1024 * 1024
    }).split(/\r?\n/).filter(Boolean);
  } catch (e) {
    die("Unable to list ZIP with system unzip: " + e.message);
  }
}

function readZipEntry(zipPath, entry) {
  try {
    return execFileSync("unzip", ["-p", zipPath, entry], {
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024
    });
  } catch (e) {
    die("Unable to read ZIP entry " + entry + ": " + e.message);
  }
}

function collectPairObjects(value, pairId, out = []) {
  if (Array.isArray(value)) {
    for (const v of value) collectPairObjects(v, pairId, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  if (value.pair_id === pairId) out.push(value);
  for (const v of Object.values(value)) collectPairObjects(v, pairId, out);
  return out;
}

function extractArm(pairObj, arm) {
  const directKeys = [
    arm,
    "arm_" + arm,
    arm + "_arm",
    "architecture_" + arm,
    arm + "_architecture",
    "plan_" + arm,
    arm + "_plan",
    "option_" + arm,
    arm + "_option"
  ];
  for (const key of directKeys) {
    if (Object.prototype.hasOwnProperty.call(pairObj, key)) {
      return { key, value: pairObj[key] };
    }
  }
  const nestedContainers = ["arms", "options", "architectures", "plans"];
  for (const key of nestedContainers) {
    const container = pairObj[key];
    if (container && typeof container === "object" &&
        Object.prototype.hasOwnProperty.call(container, arm)) {
      return { key: key + "." + arm, value: container[arm] };
    }
  }
  return null;
}

function stableJson(value) {
  function sortRec(v) {
    if (Array.isArray(v)) return v.map(sortRec);
    if (!v || typeof v !== "object") return v;
    const o = {};
    for (const k of Object.keys(v).sort()) o[k] = sortRec(v[k]);
    return o;
  }
  return JSON.stringify(sortRec(value), null, 2) + "\n";
}

const args = parseArgs(process.argv);
const packetBytes = fs.readFileSync(args.packet);
const packetSha = sha256(packetBytes);
if (packetSha !== EXPECTED_PACKET_SHA) {
  die(
    "J02 packet SHA mismatch. Expected " + EXPECTED_PACKET_SHA +
    " but got " + packetSha
  );
}

const entries = listZipEntries(args.packet);
const jsonEntries = entries.filter(n => n.toLowerCase().endsWith(".json"));
if (!jsonEntries.length) die("No JSON entries found in sealed J02 packet");

const hits = [];
for (const entry of jsonEntries) {
  let obj;
  try {
    obj = JSON.parse(readZipEntry(args.packet, entry));
  } catch {
    continue;
  }
  const pairs = collectPairObjects(obj, FROZEN_PAIR);
  for (const pair of pairs) {
    const extracted = extractArm(pair, FROZEN_ARM);
    if (extracted) {
      hits.push({ entry, pair, armKey: extracted.key, armValue: extracted.value });
    }
  }
}

if (hits.length !== 1) {
  const diagnostics = hits.map(h => ({
    entry: h.entry,
    armKey: h.armKey,
    pairKeys: Object.keys(h.pair).sort()
  }));
  die(
    "Fail-closed: expected exactly one P06 Candidate=A architecture hit, found " +
    hits.length + ". Diagnostics: " + JSON.stringify(diagnostics)
  );
}

const hit = hits[0];
const architectureText =
  typeof hit.armValue === "string"
    ? hit.armValue
    : stableJson(hit.armValue);

const surfaceInstructions = [
  "Generate the complete Korean broadcast screenplay surface for the frozen",
  "SYNC-R58 P06 Candidate architecture below.",
  "",
  "Non-negotiable constraints:",
  "- minimum 35,000 Korean characters; no maximum;",
  "- do not force a fixed sequence or scene quota;",
  "- preserve every due-now obligation and do not falsely close deferred obligations;",
  "- dialogue must not explain state merely to satisfy contracts;",
  "- express emotion/state mainly through behavior, expression shifts, props,",
  "  movement, hesitation, failed action, silence, timing, and choice;",
  "- detailed direction is allowed;",
  "- no cloned material, quota padding, generic action fallback, or repeated",
  "  full dialogue/direction templates across unrelated scenes;",
  "- do not collapse heterogeneous conflict into one confirm-record-verify-sign",
  "  procedural grammar;",
  "- preserve Episode -> Sequence -> Scene -> Surface causal provenance;",
  "- do not introduce hidden future episode knowledge.",
  "",
  "Return only the screenplay, not analysis or commentary.",
  "",
  "FROZEN SYNC-R58 P06 CANDIDATE ARCHITECTURE:",
  architectureText
].join("\n");

const payload = {
  model: args.model,
  input: surfaceInstructions,
  max_output_tokens: args.maxOutputTokens,
  store: false
};

const payloadText = JSON.stringify(payload, null, 2) + "\n";
const architectureBytes = Buffer.from(architectureText, "utf8");
const promptBytes = Buffer.from(surfaceInstructions, "utf8");
const payloadBytesOut = Buffer.from(payloadText, "utf8");

fs.mkdirSync(args.outdir, { recursive: true });

fs.writeFileSync(
  path.join(args.outdir, "p06_candidate_architecture.json.txt"),
  architectureText,
  "utf8"
);
fs.writeFileSync(
  path.join(args.outdir, "provider_surface_prompt.txt"),
  surfaceInstructions,
  "utf8"
);
fs.writeFileSync(
  path.join(args.outdir, "provider_request.json"),
  payloadText,
  "utf8"
);

const manifest = {
  schema: "SYNC_R58_PROVIDER_E2E_FROZEN_REQUEST_MANIFEST_R1",
  experiment: "SYNC_R58_PROVIDER_E2E_FULL_EPISODE_QUALIFICATION_R1",
  source: {
    judge_packet: path.basename(args.packet),
    judge_packet_sha256: packetSha,
    frozen_pair: FROZEN_PAIR,
    legally_revealed_candidate_arm: FROZEN_ARM,
    source_json_entry: hit.entry,
    source_arm_key: hit.armKey
  },
  authority: {
    physical_candidate: "SYNC-R58",
    candidate_route: "ADAPTIVE_UL16",
    integrated_runtime_sha256:
      "30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250",
    c1_transport_sha256:
      "9282eb4b3241c13e17cf032c3814674409d5efac67c26024580930ecbb633307"
  },
  request: {
    model: args.model,
    max_output_tokens: args.maxOutputTokens,
    architecture_sha256: sha256(architectureBytes),
    prompt_sha256: sha256(promptBytes),
    exact_request_body_sha256: sha256(payloadBytesOut)
  },
  status: "FROZEN_REQUEST_BUILT__NO_PROVIDER_OUTPUT_YET"
};

fs.writeFileSync(
  path.join(args.outdir, "provider_request_manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
  "utf8"
);

process.stdout.write(JSON.stringify(manifest, null, 2) + "\n");
