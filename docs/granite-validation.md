# Granite on Zo — Validation Record

**Date:** 2026-04-20 (evening) / 2026-04-21 UTC
**Host:** Zo (mickeypress.zo.computer)
**Ollama version:** 0.21.0
**Endpoint:** `http://localhost:11434`

## Status: ✅ All three models operational

| Model | Size | ID | Status |
|---|---|---|---|
| `granite4:tiny-h` | 4.2 GB | 566b725534ea | ✅ Pass |
| `granite4:350m-h` | 366 MB | 7145075ed3d6 | ⚠️ Pass with caveat |
| `granite-embedding:30m` | 62 MB | eb4c533ba6f7 | ✅ Pass |

---

## Test prompts and results

### Test 1 — `granite4:tiny-h`

**Prompt:** *"In one sentence, what is a PID controller used for in a racing AI?"*

**Response:**
> A PID (Proportional Integral Derivative) controller in a racing AI is typically used to manage the vehicle's speed and steering adjustments for optimal performance and stability during race conditions.

**Assessment:** Accurate, concise, domain-appropriate. This is our workhorse model.

### Test 2 — `granite4:350m-h`

**Prompt:** *"Answer in one short sentence: what does TORCS stand for?"*

**Response:**
> TORCS stands for Tor over SSL Relay

**Assessment:** ❌ **Hallucination.** Correct answer is "The Open Racing Car Simulator." The small model confidently fabricates domain-specific facts when the context isn't in the prompt.

### Test 3 — `granite-embedding:30m`

**Prompt:** *"A clean Corkscrew lap in TORCS."*

**Response:** 384-dimensional embedding vector, first 5 dims: `[-3.94, 1.19, -0.38, 1.02, -0.84]`

**Assessment:** Working as expected. 384 dims is the standard granite-embedding output size.

---

## Model-selection guidance (derived from this validation)

This is the rule we'll apply throughout Phases 2–4:

| Task type | Use | Why |
|---|---|---|
| Code review, architectural reasoning, controller strategy discussion | `granite4:tiny-h` | Needs domain knowledge; 350m hallucinates |
| Explaining telemetry patterns, writing blog-style prose | `granite4:tiny-h` | Quality matters more than latency |
| Well-grounded in-context tasks (summarizing a provided log, classifying a single run as crash/clean from pasted data, reformatting output) | `granite4:350m-h` | Fast, and hallucination risk is low when all facts are in the prompt |
| Similarity search across run summaries, segment descriptions, or commit messages | `granite-embedding:30m` | Purpose-built; 384-dim vectors |

**Rule of thumb:** *If the answer isn't fully in the prompt, don't trust 350m.*

---

## How to reproduce these tests

```bash
# List installed models
ollama list

# Test tiny-h
curl -s http://localhost:11434/api/generate \
  -d '{"model":"granite4:tiny-h","prompt":"YOUR PROMPT","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"

# Test 350m-h (same shape, swap model name)

# Test embedding
curl -s http://localhost:11434/api/embeddings \
  -d '{"model":"granite-embedding:30m","prompt":"YOUR TEXT"}' \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)['embedding']))"
```

---

## Granite 4 hybrid architecture → CPU inference (2026-04-21)

Validated on Windows desktop (RTX 3050 6 GB, driver 591.55, CUDA 13.1, Ollama 0.21.0).

**Finding:** `granite4:tiny-h` loads onto CPU even when GPU is detected, plenty of VRAM is free, and `OLLAMA_NUM_GPU=999` is set. Observed `ollama ps` output: `PROCESSOR: 100% CPU`.

**Root cause** (from `server.log`):

```
llama_kv_cache:          4 layers    ← transformer layers
llama_memory_recurrent:  40 layers   ← Mamba/SSM recurrent layers
CPU RS buffer size = 55.37 MiB
```

The `-h` suffix on Granite 4 models means "hybrid" — mostly Mamba (40 recurrent layers) with a few transformer layers (4) on top. Ollama 0.21.0 does not have GPU kernels for Mamba/SSM recurrent state; those layers run on CPU. With 40/44 layers forced to CPU, Ollama reports 100% CPU rather than staging a mixed load.

**Implication:** Granite 4 inference is CPU-bound in our stack today. GPU VRAM headroom is irrelevant. This applies to `granite4:tiny-h` and `granite4:350m-h` equally.

**What this affects:**
- **Token throughput** — expect ~10–20 tok/sec for `tiny-h` on a modern desktop CPU, ~50–100 tok/sec for `350m-h`. Cold-start to first token: 10–30 sec.
- **Context length** — larger contexts degrade CPU throughput quadratically. We use `contextLength: 8192` in `continue.dev` config rather than Granite 4's max 131072.
- **Heavy batch work** — offload to Zo, which has more CPU cores and always-warm RAM.

**Re-check cadence:** test again in 4–6 weeks or on each Ollama minor-version bump. Mamba GPU kernels are an active upstream development area.

---

## Open follow-ups

- [ ] ~~Re-run Test 2 on teammates' local machines~~ — solo project, moot
- [ ] Benchmark token-throughput for `tiny-h` on Zo vs. the Windows desktop — informs when to route heavy calls to Zo
- [x] When `continue.dev` gets wired up in Phase 1, reconfirm both chat models respond through that path, not just raw HTTP *(done 2026-04-21 on Windows desktop)*
- [ ] Recheck Granite 4 GPU support on each Ollama minor-version bump
