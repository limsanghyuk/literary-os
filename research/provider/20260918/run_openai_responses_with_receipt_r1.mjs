#!/usr/bin/env node
/**
 * SYNC-R58 Provider E2E receipt runner R1.
 *
 * Infrastructure only:
 * NO_ENGINE_CODE_CHANGE__PHYSICAL_AUTHORITY_UNCHANGED
 *
 * Reads an already-frozen JSON request payload, sends its exact bytes to
 * POST https://api.openai.com/v1/responses, and writes receipt artifacts.
 * OPENAI_API_KEY is read only from the process environment and is never
 * serialized into any artifact.
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

function sha256(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function die(message, code = 2) {
  process.stderr.write(message + "\n");
  process.exit(code);
}

function parseArgs(argv) {
  const out = { retryCount: 0, retryReason: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--payload") out.payload = argv[++i];
    else if (a === "--outdir") out.outdir = argv[++i];
    else if (a === "--retry-count") out.retryCount = Number(argv[++i]);
    else if (a === "--retry-reason") out.retryReason = argv[++i];
    else if (a === "--help") {
      process.stdout.write(
        "Usage: node run_openai_responses_with_receipt_r1.mjs " +
        "--payload REQUEST.json --outdir DIR " +
        "[--retry-count N] [--retry-reason TEXT]\n"
      );
      process.exit(0);
    } else {
      die("Unknown argument: " + a);
    }
  }
  if (!out.payload) die("--payload is required");
  if (!out.outdir) die("--outdir is required");
  if (!Number.isInteger(out.retryCount) || out.retryCount < 0) {
    die("--retry-count must be a non-negative integer");
  }
  return out;
}

function extractOutputText(obj) {
  if (!obj || typeof obj !== "object") return "";
  if (typeof obj.output_text === "string" && obj.output_text.length) {
    return obj.output_text;
  }
  const chunks = [];
  const output = Array.isArray(obj.output) ? obj.output : [];
  for (const item of output) {
    const content = item && Array.isArray(item.content) ? item.content : [];
    for (const part of content) {
      if (!part || typeof part !== "object") continue;
      if ((part.type === "output_text" || part.type === "text") &&
          typeof part.text === "string") {
        chunks.push(part.text);
      }
    }
  }
  return chunks.join("");
}

const args = parseArgs(process.argv);
const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) die("OPENAI_API_KEY is not set");

const payloadBytes = fs.readFileSync(args.payload);
let payload;
try {
  payload = JSON.parse(payloadBytes.toString("utf8"));
} catch (e) {
  die("Payload is not valid JSON: " + e.message);
}
if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
  die("Payload JSON must be an object");
}
if (!payload.model || typeof payload.model !== "string") {
  die("Payload must contain an explicit string model identifier");
}

fs.mkdirSync(args.outdir, { recursive: true });

const requestStartedAt = new Date().toISOString();
const requestSha = sha256(payloadBytes);

const headers = {
  "Authorization": "Bearer " + apiKey,
  "Content-Type": "application/json"
};
if (process.env.OPENAI_ORGANIZATION) {
  headers["OpenAI-Organization"] = process.env.OPENAI_ORGANIZATION;
}
if (process.env.OPENAI_PROJECT) {
  headers["OpenAI-Project"] = process.env.OPENAI_PROJECT;
}

let httpStatus = null;
let responseHeaders = {};
let rawResponse = Buffer.from("");
let parsedResponse = null;
let transportError = null;

try {
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers,
    body: payloadBytes
  });
  httpStatus = response.status;
  responseHeaders = Object.fromEntries(response.headers.entries());
  rawResponse = Buffer.from(await response.arrayBuffer());
  try {
    parsedResponse = JSON.parse(rawResponse.toString("utf8"));
  } catch {
    parsedResponse = null;
  }
} catch (e) {
  transportError = {
    name: e && e.name ? String(e.name) : "Error",
    message: e && e.message ? String(e.message) : String(e)
  };
}

const responseFinishedAt = new Date().toISOString();
const rawResponseSha = sha256(rawResponse);
const outputText = extractOutputText(parsedResponse);
const outputBytes = Buffer.from(outputText, "utf8");
const outputTextSha = sha256(outputBytes);

const requestId =
  responseHeaders["x-request-id"] ??
  responseHeaders["request-id"] ??
  null;

const receipt = {
  schema: "LITERARY_OS_OPENAI_RESPONSES_RECEIPT_R1",
  experiment: "SYNC_R58_PROVIDER_E2E_FULL_EPISODE_QUALIFICATION_R1",
  authority: {
    physical_candidate: "SYNC-R58",
    candidate_route: "ADAPTIVE_UL16",
    integrated_runtime_sha256:
      "30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250",
    c1_transport_sha256:
      "9282eb4b3241c13e17cf032c3814674409d5efac67c26024580930ecbb633307"
  },
  endpoint: "https://api.openai.com/v1/responses",
  request_started_at: requestStartedAt,
  response_finished_at: responseFinishedAt,
  http_status: httpStatus,
  provider_response_id:
    parsedResponse && typeof parsedResponse.id === "string"
      ? parsedResponse.id
      : null,
  provider_request_id: requestId,
  requested_model: payload.model,
  provider_model:
    parsedResponse && typeof parsedResponse.model === "string"
      ? parsedResponse.model
      : null,
  usage:
    parsedResponse && parsedResponse.usage
      ? parsedResponse.usage
      : null,
  hashes: {
    exact_request_body_sha256: requestSha,
    raw_response_body_sha256: rawResponseSha,
    extracted_output_text_sha256: outputTextSha
  },
  output_text_bytes: outputBytes.length,
  retry_count: args.retryCount,
  retry_reason: args.retryReason,
  transport_error: transportError,
  status:
    transportError
      ? "TRANSPORT_FAILURE"
      : (httpStatus !== null && httpStatus >= 200 && httpStatus < 300)
        ? "PROVIDER_RESPONSE_RECEIVED"
        : "PROVIDER_HTTP_FAILURE"
};

fs.writeFileSync(
  path.join(args.outdir, "provider_raw_response.bin"),
  rawResponse
);
fs.writeFileSync(
  path.join(args.outdir, "provider_output_text.txt"),
  outputText,
  "utf8"
);
fs.writeFileSync(
  path.join(args.outdir, "provider_receipt.json"),
  JSON.stringify(receipt, null, 2) + "\n",
  "utf8"
);

process.stdout.write(JSON.stringify(receipt, null, 2) + "\n");

if (receipt.status !== "PROVIDER_RESPONSE_RECEIVED") {
  process.exit(1);
}
