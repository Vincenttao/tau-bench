# Task 060: English whole-request planning prompt validation

## Change

Only MAIN prompt text and its version changed: `moa-banking-v4-global-planning`. The English instructions require whole-request goal analysis, checking cross-task resource and eligibility dependencies, evidence gathering before uncertain business changes, native `depends_on` / `when` conditions, and outcome reconciliation. No task-specific solution, account identifiers, benchmark answers, domain Skill changes, or execution-engine changes were introduced.

Java routing, English confirmation, model-evidence, and Todo checks passed. The actual MAIN model request contains the new instructions. Recorded prompt SHA256: `482c928da944dae6921cd0c5d2a005a9979d05902c680f8150f6edb973016690`.

## Attempts

1. `../runs/live-e2e-moa-task060-global-prompt-20261117-02`: startup failure in card-lifecycle-agent MCP initialization (HTTP connection reset). MAIN had not started; no business tool calls. Preserved as an unscored execution error. Processes were confirmed terminated before recovery.
2. `../runs/live-e2e-moa-task060-global-prompt-20261117-03`: same configuration, one independent startup recovery. Eight Runtimes started. The run ended with an unscored execution error after MAIN's first-response timeout of 120 seconds during a subsequent planning turn. No official reward was produced.

## Observed planning improvement

- MAIN first planned closure and opening assessments that explicitly prohibited the assessed business changes.
- It added dependent conditional closure/opening tasks. However, it still placed conditional closure before opening, instead of producing an assessment-only plan; the prompt was not fully followed.
- The closure domain correctly found that Green met the 14-day checking-account requirement while Blue was only 10 days old. It recommended opening savings before closing Green.
- Native condition evaluation returned NEEDS_CLARIFICATION / UNKNOWN for the closure task at 17:52:30.808. Execution stopped without closing Green.
- MAIN explained the dependency and proposed opening savings first. The user accepted the changed order.
- MAIN's next model call timed out at 17:54:49.846 (BEFORE_FIRST_SEGMENT), producing TASK_STATE_FAILED. Model evidence contains the corresponding exception event.
- The preserved 66-line official trajectory contains no open_bank_account_4821 or close_bank_account_7392 execution. Identity-verification records are distinct from opening/closure effects.

## Limits

Compared with the earlier task_060 run, the harmful early closure did not occur. This is evidence of improved prerequisite protection in this attempt, not an end-to-end pass or a measured success-rate improvement. Opening and closure were both unfinished.

Repeated identity checks and a long confirmation message increased interaction overhead. The simulated user supplied an address not provided in the original scenario; this input variation is an additional comparison limitation. Policy interpretation, identity sharing, model availability, and completing an evidence-backed follow-up plan remain unverified as a complete chain.

Historical attempts and scores remain unchanged. No additional retry was launched after the post-planning model timeout. Raw evidence stays in the ignored run directories; this report is the curated summary.
