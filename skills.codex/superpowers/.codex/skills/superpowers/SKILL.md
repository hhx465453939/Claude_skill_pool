---
name: superpowers
description: Universal AI task processing framework based on systematic thinking and task decomposition. Automatically activates for complex tasks: creating features, deep analysis, solution design, planning, multi-step execution. Not for simple single-step queries.
version: 2.0.0
---

# Superpowers — Universal AI Task Processing Framework

Transforms AI agents into genuine problem-solving partners. Covers software development and all complex tasks through strict TDD practices and systematic methodology.

## Core Principles

1. **Test-Driven Development** — No failing test, no production code (dev tasks)
2. **Systematic Over Ad-Hoc** — Structured decomposition, no guesswork
3. **Complexity Reduction** — Simplicity is the primary goal
4. **Evidence Over Claims** — Verify before declaring success
5. **Efficiency First** — Maximize token efficiency; batch and parallelize

---

## Phase 0: Task Complexity Assessment

**Complex task** (launch Superpowers):
- Requires multi-step reasoning or multi-round info collection
- Involves multiple sources or tool calls
- Requires creative thinking or solution design
- Involves trade-off decisions or uncertainty
- Requires structured output (report / doc / plan)
- Cannot be fully covered in one reply

**Simple task** (answer directly):
- Single-fact query
- Single file operation
- Direct-answer question
- Single-step operation

**Auto-trigger**:
- ✅ "Help me create / analyze / design / optimize / solve / plan..."
- ✅ Involves multiple steps or sub-tasks
- ❌ Single query / direct answer / single step

---

## Universal Workflows (Non-dev Tasks)

### Workflow A: General Brainstorming
**Use when**: Deep thinking / design / planning / analysis

1. Understand task — clarify goals, constraints, success criteria
2. Ask clarifying questions — one at a time
3. Explore options — propose 2-3 approaches with trade-offs
4. Present in chunks — present each chunk, get confirmation
5. Structured output — generate doc / report
6. Validate — confirm result meets requirements

**Output**: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

### Workflow B: Task Decomposition & Execution
**Use when**: Multi-step execution tasks

1. Decompose — break into 2–5 min atomic tasks
2. Prioritize — order by dependencies and importance
3. Execute — step by step, verify each step
4. Report progress — periodic check-ins
5. Summarize — aggregate all sub-task results

### Workflow C: Information Gathering & Synthesis
**Use when**: Multi-source info collection tasks

1. Analyze info needs — what and why
2. Identify sources — search / files / APIs
3. Parallel collection — maximize parallelism to save tokens
4. Synthesize — deduplicate, verify
5. Structured output — report / document

### Workflow D: Solution Design & Decision
**Use when**: Designing solutions or making decisions

1. Requirements analysis — understand the root problem and constraints
2. Generate options — 2-3 viable solutions
3. Evaluate — technical feasibility, cost, risk, maintainability, UX
4. Recommend — best option with reasoning
5. Implementation plan — if needed

---

## Development Workflow

```
Requirement → Brainstorming → Design Spec → Writing Plans → TDD → Code Review → Finish Branch
```

### Brainstorming
**Trigger**: Before any creative work

- Explore context; ask one clarifying question at a time
- Propose 2-3 options with trade-offs
- Present design in chunks, get per-chunk approval
- **Hard gate**: must get design approved before touching any code
- Output: `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

### Writing Plans
**Trigger**: After approved design, before touching code

- Map file structure; write fine-grained tasks (2–5 min each)
- Every task has exact paths, complete code, verification commands
- Output: `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

### Test-Driven Development
**Trigger**: Before implementing any feature or bug fix

**Iron rule**: No failing test → no production code

**RED-GREEN-REFACTOR**:
1. **RED** — Write one failing test (one behavior, clear name, real code)
2. **Verify RED** — Run it, confirm FAIL (not error), fail reason = missing feature
3. **GREEN** — Write minimal code to pass; don't add extra behavior
4. **Verify GREEN** — Run it, confirm PASS; all other tests still pass
5. **REFACTOR** — Only after green; clean up; keep tests green; no new behavior

### Code Review
**Trigger**: Between tasks, automatic

- Report issues by severity (Critical / High / Medium / Low)
- Critical blocks progress
- Check: spec compliance, code quality, TDD, DRY/YAGNI

### Subagent-Driven Development
**Trigger**: Have a plan + platform supports sub-agents

- Fresh sub-agent per task; two-stage review (spec compliance → code quality)

### Using Git Worktrees
**Trigger**: After design approval, before implementation

- Create isolated workspace on new branch; verify clean test baseline

### Finishing a Development Branch
**Trigger**: Tasks complete

- Verify tests; present options (merge / PR / keep / discard); clean worktree

---

## Token Efficiency Strategy

| Principle | Practice |
|---|---|
| Batch operations | Collect all needed info in one shot |
| Parallel processing | Run independent tasks concurrently |
| Structured output | Return complete result at once, never step-by-step |
| Cache first | Prefer existing info (memory / files / cache) |
| Direct tools | Choose the most direct tool; avoid unnecessary steps |

---

## Output Contract

Every response must satisfy:
- [ ] Fully covers the user's requirement
- [ ] Information is accurate and verifiable
- [ ] Clear structure, easy to read
- [ ] No redundant content
- [ ] Complex tasks produce structured output (doc / report / plan)

---

## Resources

| Resource | Path | Purpose |
|---|---|---|
| `references/quick-start.md` | references/ | Skills quick-reference and core workflows |
| `scripts/tdd-checklist.md` | scripts/ | Full TDD checklist for dev tasks |
| `templates/design-spec-template.md` | templates/ | Design spec document template |
| `templates/implementation-plan-template.md` | templates/ | Implementation plan template |

**Path conventions by runtime:**
- **Codex (this file):** supporting files are siblings of this `SKILL.md`; e.g., `scripts/tdd-checklist.md` relative to skill root.
- **Claude mirror:** all supporting files under `.claude/skills/superpowers/`; e.g., `.claude/skills/superpowers/scripts/tdd-checklist.md`.
- **Gemini mirror:** same layout as Codex; `scripts/tdd-checklist.md` relative to skill root.
