# 05 — Granite workflow

How to use Granite productively during development. Two channels: **continue.dev in VSCode** (most work), and **direct Ollama API on Zo** (batch/automated work).

**Prerequisites:** continue.dev configured per `../setup.md` step 5, or Ollama running on Zo.

---

## Decision: which model, which channel?

| Task | Model | Channel |
|---|---|---|
| Asking "why does this controller crash on turn 6?" | `granite4:tiny-h` | continue.dev chat |
| Reviewing a diff / code quality | `granite4:tiny-h` | continue.dev chat |
| Inline autocomplete while typing | `granite4:350m-h` | continue.dev autocomplete |
| Batch-summarizing N run `summary.md` files | `granite4:tiny-h` | Ollama API on Zo (curl / script) |
| Similarity search across run notes / commits | `granite-embedding:30m` | Ollama API |
| Quick "reformat this JSON" in a script | `granite4:350m-h` | either |

**Hard rule (from `../granite-validation.md`):** if the answer isn't already in the prompt, don't use `350m-h`. It hallucinates on domain-specific facts.

---

## Channel A — continue.dev in VSCode

This is where most of the Phase 3 work happens — interactive code review with Granite.

### Effective prompt patterns

**Code review:**
> Review `src/driver_baseline.py`. I crashed on turn 6 of Corkscrew. Here's the last 2 seconds of telemetry leading up to the crash: [paste `segments.csv` row]. What in the controller logic would cause this?

**Controller strategy:**
> I'm using PID for steering. Throttle is lookup-table-based, keyed on segment_id. What are 3 reasons the PID steering might overshoot on a fast left-right chicane like the Corkscrew sequence?

**Explaining a change:**
> Explain in 1 paragraph what this diff does and what the expected effect on lap time is: [paste diff].

### Anti-patterns

- ❌ "Make my driver faster" — too vague, Granite will hallucinate improvements
- ❌ "What does TORCS stand for?" — don't ask context-free trivia of 350m
- ❌ Pasting 2000 lines of telemetry — chunk it; Granite reasons better over focused excerpts

---

## Channel B — Ollama API on Zo

For batch work or automation. Ollama is already installed and running on Zo (see `../granite-validation.md`).

### Quick chat call

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"granite4:tiny-h","prompt":"Summarize this run in 2 bullets: [paste summary.md]","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

### Embedding call

```bash
curl -s http://localhost:11434/api/embeddings \
  -d '{"model":"granite-embedding:30m","prompt":"Corkscrew turn 6 overshoot due to steering overshoot"}' \
  | python3 -c "import sys,json; v=json.load(sys.stdin)['embedding']; print(len(v))"
```

384-dim output. Use for semantic search over accumulated run notes / commits.

---

## Phase-3 workflow: the feedback loop

The core development loop we're building toward:

1. Run a race → produce `runs/<timestamp>/`
2. Auto-summarize with `granite4:tiny-h` → writes to `summary.md`
3. A/B compare against baseline → update `leaderboard.md`
4. Ask Granite: "diff this run's segments vs. the prior best run, what stands out?"
5. Decide what to change, make the code change (use continue.dev)
6. Commit with a message that references the run_id so it's searchable
7. Repeat

Every loop iteration **compounds the dataset**. That's the moat.

---

## Logging Granite's suggestions

When Granite suggests a change you actually apply, log it in `docs/granite-suggestions.md` (create if missing) so the blog can reference real examples:

```markdown
## <date> — <short title>
- Run: `runs/<timestamp>/`
- Prompt: [short version]
- Suggestion: [what Granite said]
- Applied: yes/no
- Result: lap time change, crash count change
```

This is **blog-rubric gold**. The mission brief rewards teams that show how they used IBM Granite.

---

## Next

- `06-troubleshooting.md` — when things break
- `../granite-validation.md` — raw validation test results
