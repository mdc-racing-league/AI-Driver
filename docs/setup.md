# Team Setup Guide

End-to-end **one-time** setup that every teammate should complete during **Phase 1 (Apr 27 – May 3)**.

> **Not what you're looking for?**
> - Day-to-day runbook (how to launch the sim, capture telemetry, use Granite): `simulation-guide/`
> - Project roadmap and strategy: `roadmap.md`
> - Granite model-selection rules: `granite-validation.md`

Primary source docs:
- `TORCSRegtoSubmission0901-Mission Brief-Detailed (1).pdf`
- `Wtorcs-ollama-instructions.pdf`

---

## 1. Install VSCode

Download: https://code.visualstudio.com/

## 2. Install Ollama

- **Windows/Mac/Linux:** https://ollama.com/download
- Before installing, check if Ollama is already on your machine:
  ```
  ollama --version
  ```
  If it returns `ollama version is 0.21.0` (or similar), you're done — skip the installer.
- After install, confirm it's running:
  ```
  ollama --version
  ollama list
  ```
- Optional: confirm the service is up:
  ```
  Get-Process ollama -ErrorAction SilentlyContinue    # Windows
  pgrep ollama                                        # Mac/Linux
  ```
  If no process shows, launch Ollama from your Start Menu / Applications, or run `ollama serve`.

## 3. Pull IBM Granite models

From the terminal:

```
ollama pull granite4:tiny-h
ollama pull granite4:350m-h
ollama pull granite-embedding:30m
```

Optional bigger model if your laptop has ≥16GB RAM:

```
ollama pull granite4:small-h
```

Verify models are present:

```
ollama list
```

## 4. Install continue.dev VSCode extension

1. Open VSCode → Extensions panel
2. Search `continue.dev` and install
3. Reload VSCode

## 5. Configure continue.dev to use Granite via Ollama

Create/edit `~/.continue/config.yaml` (Mac/Linux) or `%USERPROFILE%\.continue\config.yaml` (Windows):

```yaml
name: Local Config
version: 1.0.0
schema: v1

models:
  - name: Granite 4 Tiny
    provider: ollama
    model: granite4:tiny-h
    apiBase: http://localhost:11434
    roles:
      - chat
      - edit
      - apply
    capabilities:
      - tool_use
    defaultCompletionOptions:
      contextLength: 8192
      # Granite 4 supports up to 131072, but on CPU-bound hybrid inference
      # (see granite-validation.md) larger contexts tank throughput.
      # 8192 is enough to paste a full driver file; bump if you need more.

  - name: Granite 4 350m
    provider: ollama
    model: granite4:350m-h
    roles:
      - autocomplete

  - name: granite-embedding:30m
    provider: ollama
    model: granite-embedding:30m
    roles:
      - embed
    embedOptions:
      maxChunkSize: 512
```

Open the Continue chat panel in VSCode → click the gear → pick **Granite 4 Tiny** as your chat model.

## 6. Install TORCS

### Windows (easy path)
1. Download the TORCS Quick Start bundle: https://ibm.biz/TORCSQuickStartExt
2. Extract to a path without spaces — `C:\torcs\` recommended
3. Follow the bundled README

### Mac (via Wine)
1. Install Wine: https://www.winehq.org/
2. Download the Mac extras: https://ibm.box.com/v/MacOSExtraExt
3. Follow Mac-specific instructions from the extras.

### Note on GPU expectations

If you have an NVIDIA GPU, you may notice Ollama reports `100% CPU` in `ollama ps` even though CUDA is detected. **This is expected for Granite 4 hybrid models** — see `granite-validation.md` section "Granite 4 hybrid architecture → CPU inference." Don't burn time on GPU tuning; accept ~10–20 tok/sec on CPU and offload heavy batch work to Zo.

## 7. Clone this repo

```
git clone https://github.com/LouisRodriguez12101815/ibmRacingLeague.git
cd ibmRacingLeague
```

## 8. Run the wtorcs baseline

**Setup is done — switch to the runbook.** Follow `simulation-guide/01-quickstart.md` to verify the sim launches, then continue through `02-launching-torcs.md` and (once Phase 2 lands) `03-running-our-driver.md`.

## 9. Smoke test: Granite review-your-code

In VSCode Continue chat:

> Review `src/driver_baseline.py`. What assumptions am I making about sensor
> values that could cause a crash on the Corkscrew downhill?

If Granite responds coherently, setup is complete.

> Note: `src/driver_baseline.py` doesn't exist until Phase 2. Until then, substitute any Python file in the repo (e.g. `scripts/log_telemetry.py`) to verify Granite is wired up correctly.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ollama: command not found` | Restart terminal after install; check PATH |
| Continue shows "no models" | Restart VSCode; check `config.yaml` path and indentation |
| TORCS won't launch on Mac | Confirm Wine is installed and PATH is correct |
| Ollama slow on your laptop | Expected — Granite 4 hybrid runs CPU-only in Ollama 0.21.0. Close Teams/Copilot/Discord to free RAM, not VRAM. |
| `ollama ps` shows `100% CPU` despite GPU | Known limitation of Granite 4 hybrid in Ollama 0.21.0 — see `granite-validation.md`. Not a config issue; accept it and move on. |
| Continue "I don't have access to files" | You haven't opened a workspace folder in VSCode. Use `File → Open Folder` on the repo clone, then prefix chat questions with `@codebase` or `@file path/to/file.py`. |
| First Continue response takes 30+ sec | Cold-start model load + CPU token generation. Only affects the first message; subsequent ones in the same session are faster. |

## Phase 1 sign-off

When done, check your name off in `roadmap.md` Phase 1 section and push to `main`.
