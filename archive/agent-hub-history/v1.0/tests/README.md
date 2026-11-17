# English baseline E2E verification

Run from the tau3 repository root, outside the sandbox, with Python 3.12, JDK 21, Maven and the existing local Java dependencies. Provide `OPENAI_API_KEY` through the process environment. The scripts never persist the key.

```bash
.venv312/bin/python experiments/agent-hub-banking/v1.0/tests/run_english_e2e.py \
  --output experiments/agent-hub-banking/v1.0/runs/english-e2e-NEW
```

This command makes external model calls. It runs one `task_054` attempt, Skill 3.2.0, English, seed 300, one trial and one concurrent episode. It builds the bridge, verifies the deterministic Java/MCP fixture, probes the configured gateway, executes the official episode and analyzes its result. An existing output directory is rejected. No automatic episode retry and no cumulative token budget are configured. Core completion, bridge event and episode timeouts are 1200, 1500 and 2400 seconds respectively.

The target is the existing DeepAgent baseline. Agent Hub adoption, effect authorization, durable receipts and recovery controls are not installed. This is neither a B0/B1 paired experiment nor a production bank test. `task_054` uses customer dialogue and agent tools; its `user_tools` list is empty, so this case cannot validate user-side business writes.

After a scored episode, perform strict offline state reconstruction using the existing `python/replay_final_state.py`, with the English checkout in `PYTHONPATH` and `TAU2_DATA_DIR`. Save `strict-state-reconstruction.json` in the run root. Preserve a `source-freeze.json` and its `frozen/` files as recorded in the completed batch. These review artifacts are separate from the execution runner.

```bash
.venv312/bin/python experiments/agent-hub-banking/v1.0/tests/verify_english_e2e.py \
  experiments/agent-hub-banking/v1.0/runs/english-e2e-NEW \
  --output experiments/agent-hub-banking/v1.0/reports/english-e2e-NEW/verification.json
```

The verifier writes a new report and leaves raw evidence untouched. It checks the official outcome, English runtime and dialogue, frozen sources, deployed Skill hashes, raw MCP receipt hashes, operation ordering and adjusted credit limit. A completed run may still have a failed official score. The JSON checks and official status, not a successful shell exit alone, determine the result.
