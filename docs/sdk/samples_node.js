// Literary OS PublicSDK — Node.js/fetch 샘플 코드 (ADR-117)
// 의존성: node-fetch (npm install node-fetch)

const fetch = require("node-fetch");
const BASE = process.env.LOS_API_URL || "http://localhost:8080";
const API_KEY = process.env.LOS_API_KEY || "YOUR_API_KEY";

const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

// 1. analyze
async function analyze(text, context = "") {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ text, context, lang: "ko" }),
  });
  const data = await res.json();
  console.log("품질:", data.quality.overall, "이슈:", data.issues);
  return data;
}

// 2. generate
async function generate(title, characters, setting, conflict) {
  const res = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title, characters, setting, conflict, tone: "dramatic", max_rounds: 3 }),
  });
  const data = await res.json();
  console.log("씬:", data.scene_text);
  return data;
}

// 실행
(async () => {
  await analyze("영수는 창문을 바라보았다. 눈물이 고였다. 배신감이 폭발했다.");
  await generate("운명의 교차로", ["이지수", "박민호"], "비 오는 골목길", "비밀이 드러나다");
})();
