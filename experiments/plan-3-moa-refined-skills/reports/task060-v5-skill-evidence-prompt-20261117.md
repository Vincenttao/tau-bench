# Task 060 follow-up: v5 Skill-evidence prompt

## Reason

The DeepSeek official-endpoint E2E completed without a model timeout but scored 0. MAIN ignored the v4 whole-request guidance and planned Green Account closure before savings opening, without prerequisite assessment or dependencies. Closing Green removed the only checking account that met the savings-opening tenure requirement.

## Revision

MAIN prompt version is now `moa-banking-v5-skill-evidence-plan`. For multiple potentially related operations it requires this sequence:

1. Identify every outcome, relevant domain and resource-changing operation.
2. If authoritative prerequisites or sequencing facts are missing, create an assessment-only `stage_plan`.
3. Require each relevant domain Agent to use its own loaded Skill and authoritative policy sources. Assessment queries must prohibit business writes and return prerequisites, affected resources, unresolved facts and feasible sequencing.
4. Do not mix assessment tasks with affected writes in the same frozen plan. Complete the assessment plan, reconcile the evidence and stop.
5. Use a subsequent customer request through the native planning flow to create the evidence-backed write plan.
6. Use `depends_on` and `when`, obtain native confirmation and execute writes in dependency order. Missing or ambiguous prerequisites cannot authorize a dependent write.

This preserves current MOA boundaries: MAIN does not read domain Skills itself, a frozen plan is not dynamically reordered, and domain Agents retain business-policy ownership.

## Verification

`java/check-routing.sh` passed all four Java checks: slow routing, English confirmation, MAIN model evidence and Todo transition. Two focused Python prompt/runtime assertions passed.

## Live E2E regression

Run: `runs/live-e2e-moa-task060-deepseek-direct-20261117-03`

- Endpoint/model: `https://api.deepseek.com`, `deepseek-flash`.
- Result: official reward `1.0`, `business_pass=true`, termination `user_stop`.
- Duration: `546.775` seconds.
- MAIN model calls: 35 requests and 35 responses. The maximum measured MAIN request-to-response interval was `30.949` seconds; no MAIN model timeout occurred.
- First plan: read-only closure and savings-opening assessments. No business write occurred in that plan.
- Evidence found: Green was OPEN with `$0`; Blue was OPEN with `$1,500`; Green met the tenure prerequisite, whereas the recently opened Blue account did not. The safe sequence was therefore savings opening before Green closure.
- Write order: Silver Plus savings was opened first as account `89fbc464fa6f2c5e`; Green checking `58d57780cc15e32d` was closed later. The final read-back showed Green CLOSED, Blue OPEN with `$1,500`, and Silver Plus OPEN with `$0`.
- The closure domain performed another read-only assessment of payroll/recurring-payment effects before closure. This added latency and model/tool calls, but it did not perform an unsafe write and the official task still passed.

This is a real single-case regression using an already exposed task. It verifies that this prompt revision can correct the observed task-060 ordering failure; it is not an unbiased benchmark score or proof of general improvement across the cohort. Architecture acceptance remains `not-yet-evaluated` in the generated artifact.
