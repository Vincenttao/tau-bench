# Task 060: DeepSeek official endpoint E2E

## Configuration

- Purpose: development diagnostic, not formal comparison.
- API base: `https://api.deepseek.com`.
- Requested and observed model: `deepseek-flash`.
- MAIN prompt: `moa-banking-v4-global-planning`.
- Model request timeout: 120 seconds; model retries: 0.
- Driver: partial `moa-pilot`, official user simulator and official evaluator.
- Credential was supplied interactively and was not persisted.

The diagnostic runner now supports explicit, manifest-recorded `--api-base` and `--model` overrides. This keeps the four-arm formal comparison profile unchanged.

## Attempts

### 01: startup resource exhaustion

Run: `../runs/live-e2e-moa-task060-deepseek-direct-20261117-01`.

The official user simulator made one successful `deepseek-flash` call. Five domain Runtimes became ready, but the sixth (`transaction-dispute-agent`) did not finish local MCP initialization within the 120-second host-ready wait. MAIN never started. The run ended unscored with `_queue.Empty`; this is not a model timeout result.

At diagnosis time only about 494 MiB memory remained available and swap was full. Domain Runtimes were also attempting peer discovery against placeholder URLs they never use. The pilot was revised to cap each JVM heap at 256 MiB and configure remote domain discovery only for MAIN. Java routing checks and 11 focused Python checks passed before retry.

### 02: completed official episode

Run: `../runs/live-e2e-moa-task060-deepseek-direct-20261117-02`.

All seven domain Runtimes and MAIN became ready. The official episode completed and was scored:

| Field | Result |
|---|---|
| Status | scored |
| Reward | 0.0 |
| Termination | user_stop |
| Duration | 185.858 seconds |
| Business pass | false |
| Architecture acceptance | not-yet-evaluated |

MAIN made seven model calls. All seven succeeded with `deepseek-flash`; there were no model exceptions or 120-second timeouts.

| MAIN call | Time | Input tokens | Output tokens | Result |
|---|---:|---:|---:|---|
| 1 | 14.970 s | 4,937 | 2,373 | stage_plan |
| 2 | 1.126 s | 7,773 | 28 | stage_bind_next |
| 3 | 0.391 s | 8,147 | 24 | stage_bind_next |
| 4 | 0.684 s | 8,527 | 24 | stage_finalize |
| 5 | 0.724 s | 8,777 | 24 | stage_execute_next |
| 6 | 0.915 s | 9,432 | 24 | stage_execute_next |
| 7 | 7.494 s | 10,344 | 1,023 | final response |

## Business failure

The model endpoint change removed the observed MAIN timeout but did not correct the task planning failure. MAIN's first plan contained two independent tasks in this order:

1. Close Green Account.
2. Open a savings account.

It did not add an evidence-gathering task, `depends_on`, or a `when` condition. The closure domain then closed Green successfully. The opening domain subsequently found that savings eligibility requires an active checking account held for at least 14 days. Green had met the requirement, but Blue had only 10 days of tenure and would reach eligibility on 2025-11-18. The savings account was not opened. The customer requested transfer to a human agent, and the evaluator assigned reward 0.

This establishes two separate conclusions:

- Transport/model availability: the DeepSeek official endpoint completed the real Java MAIN path without model timeout in this episode.
- MOA behavior: the global-planning prompt was present but not followed by `deepseek-flash` on the initial plan. The irreversible closure was executed before the prerequisite evidence was obtained, so the original two-part goal failed.

Raw runs remain ignored execution evidence. This report is the curated repository artifact.
