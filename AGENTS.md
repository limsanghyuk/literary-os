<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **literary-os** (41586 symbols, 68256 relationships, 242 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/literary-os/context` | Codebase overview, check index freshness |
| `gitnexus://repo/literary-os/clusters` | All functional areas |
| `gitnexus://repo/literary-os/processes` | All execution flows |
| `gitnexus://repo/literary-os/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

---

## 🔴 필수 학습 (Critical Loading) — 모든 작업 시작 전

작업 시작 전 반드시 읽고 컨텍스트에 포함:

1. `docs/sessions/INDEX.md` (전체 색인·정본 순서)
2. `docs/sessions/2026-06-07_MASTER_synthesis_priorities.md` (현 시점 종합·우선순위)
3. `docs/sessions/2026-06-07_home_handoff_v3.md` (이어작업 정본)
4. `CLAUDE.md` (RULE-0) · `docs/workflow/DEV_PROTOCOL_v3.0.md`

**위 파일이 컨텍스트에 없으면 절대 코드 작성 금지.**
(주: GitNexus 인덱스 = V745 재인덱싱 완료 — `literary-os`: 41,586 symbols · 68,256 relationships · 242 flows.)

docx 추출:
```bash
python -c "
from docx import Document
d = Document('docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.docx')
for p in d.paragraphs:
    if p.text.strip(): print(p.text)
" | head -200
```
