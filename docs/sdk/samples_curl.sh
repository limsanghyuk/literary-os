#!/usr/bin/env bash
# Literary OS PublicSDK — cURL 샘플 (ADR-117)
BASE="${LOS_API_URL:-http://localhost:8080}"
API_KEY="${LOS_API_KEY:-YOUR_API_KEY}"
HDR=(-H "Content-Type: application/json" -H "X-API-Key: $API_KEY")

# 1. analyze
echo "=== analyze ==="
curl -s -X POST "$BASE/analyze" "${HDR[@]}" \
  -d '{"text":"영수는 창문을 바라보았다. 눈물이 고였다. 배신감이 폭발했다.","lang":"ko"}' | python3 -m json.tool

# 2. repair
echo "=== repair ==="
curl -s -X POST "$BASE/repair" "${HDR[@]}" \
  -d '{"text":"짧은 씬이다.","issues":["too_few_sentences"],"target_score":0.75}' | python3 -m json.tool

# 3. predict
echo "=== predict ==="
curl -s -X POST "$BASE/predict" "${HDR[@]}" \
  -d '{"context":"두 사람이 마주쳤다. 분위기가 묘했다.","n":2,"style_hint":"melodrama"}' | python3 -m json.tool

# 4. generate
echo "=== generate ==="
curl -s -X POST "$BASE/generate" "${HDR[@]}" \
  -d '{"title":"운명의 교차로","characters":["이지수","박민호"],"setting":"골목길","conflict":"비밀"}' | python3 -m json.tool

# 5. health
echo "=== health ==="
curl -s "$BASE/health"
