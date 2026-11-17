# Task 054 v5 DeepSeek live E2E regression

## Selection basis

`task_054` was selected before execution because an earlier real run had official reward `0`. That run filed the transaction dispute and ordered the replacement card before completing the credit-limit increase (CLI), which made the CLI ineligible. The task is independent of task 060 and exercises a three-way dependency: CLI, transaction dispute and replacement card.

## Current run

- Evidence directory: `runs/live-e2e-moa-task054-deepseek-v5-20261117-01`
- Endpoint/model: `https://api.deepseek.com`, `deepseek-flash`
- MAIN prompt: `moa-banking-v5-skill-evidence-plan`
- Official result: `reward=0.0`, `business_pass=false`, termination `user_stop`
- Duration: `340.207` seconds
- MAIN model calls: 25 requests and 25 responses
- Maximum MAIN request-to-response interval: `16.736` seconds; no MAIN model timeout occurred

## What improved

The first plan was assessment-only. No dispute, replacement-card order or CLI write was made. The domain assessments retrieved the key facts: no existing dispute, no pending replacement order, no prior CLI request and three consecutive on-time payments. MAIN explained the conflict before any eligibility-changing write, and the simulated customer agreed to process the CLI first if safe.

This corrects the earlier unsafe ordering behavior. It did not, however, complete the business task.

## Why this run failed

The subsequent assessment cycles failed inside domain Todo handling:

1. `card-lifecycle-agent`: `Batch update failed: Missing required field: 'id'`.
2. `transaction-dispute-agent`: `Task with id 'provisional_credit' not found`.
3. A retry in the same persistent domain session then failed with `Batch append failed: Task with ID 'sequencing' is duplicated`.

MAIN accurately reported that no business changes had been made. The simulated customer declined further retries and requested a human transfer. The final database therefore lacked all three required business outcomes, so official reward `0` is expected.

The trace also contains two attempts to unlock `log_verification` as a discoverable tool, which returned `Unknown agent tool 'log_verification'`. `log_verification` is a native tool and should be called directly. This was not the final terminating exception, but it is another tool-selection defect to address.

## Assessment

The v5 prompt generalized the intended safety behavior: read Skills/policy, assess globally, and avoid unsafe writes. The remaining blocker is not the DeepSeek connection or MAIN ordering prompt. It is the domain Agent Todo implementation/prompt contract across continuation and retry: generated task IDs are updated without a valid Todo identifier, referenced after they no longer exist, or appended again into a persistent session.

This is a real regression result on an exposed failed case. It is not an unbiased benchmark result and it does not prove general score improvement. Architecture acceptance remains `not-yet-evaluated`.

## Follow-up revision

The project boundary now validates model-generated `todo_modify` batches before Core/A2A execution. For `update` and `append`, every item must have a non-empty, batch-unique id; update ids must already exist and append ids must not exist. An invalid batch is changed to an authoritative `todo_list` read inside the same ReAct loop so the model can recompute the set without aborting and rolling back the enclosing A2A request.

The domain prompt now states the same persisted-set contract and requires a fresh `todo_list` after rejection, resume or retry. A Java regression covers missing ids, unknown update ids, existing append ids and duplicate ids. The complete routing check passes after this change.

## Follow-up live E2E

Run: `runs/live-e2e-moa-task054-deepseek-v5-20261117-02`

- Official result: `reward=0.0`, `business_pass=false`, termination `user_stop`.
- Duration: `636.093` seconds.
- MAIN model calls: 46 requests and 46 responses; maximum request-to-response interval `19.396` seconds. No MAIN timeout occurred.
- Business order was corrected: the `$2,500` CLI was submitted and approved first, changing the limit from `$5,000` to `$7,500`; the CloudSync dispute was then filed; the replacement card was ordered last. The final customer stopped after confirming all three goals were handled.
- The early assessment still encountered two Todo validations not covered by the first boundary revision: more than one `in_progress` item, and an update item missing `status`. These caused A2A failures, although later fresh customer requests allowed the three business writes to complete.
- Official action checks matched the CLI submission/approval and the principal reads. They did not match three reference actions: no successful `log_verification`; the replacement used customer-requested standard shipping (`expedited_shipping=false`) while the reference fixes `true`; and the dispute used `card_action=keep_active` before the later replacement while the reference fixes `cancel_and_reissue`.

The official zero is therefore retained. Operationally, the three customer goals were completed in the safe order, but this run does not pass the benchmark's exact DB/action reference. The Todo boundary still needs status/cardinality validation, and the dispute/replacement pair should be planned as one linked write so that `cancel_and_reissue` and the replacement receipt remain consistent. Standard shipping must not be changed merely to match a hidden reference when the customer explicitly requests it.

## Todo recovery revision 2

The boundary now loads the persisted id/status map before each `todo_modify` update or append. It rejects a batch before Core/A2A when an item lacks an explicit supported status or when the computed post-call state would contain more than one `in_progress` item. As with invalid ids, the rejected call is replaced by `todo_list` so the model receives authoritative state and can recompute a complete transition in the same ReAct loop.

The prompt requires the model to calculate the post-call state, complete the current active item in the same update that starts the next item, and reread Todo after rejection/resume/retry. Regression coverage now includes missing status and multiple-active-state cases in addition to missing, unknown and duplicate ids. Shared Java compilation and the complete MOA routing check pass. This second recovery revision has not yet had a fresh live E2E run.

## Todo recovery revision 2 live E2E

Run: `runs/live-e2e-moa-task054-deepseek-v5-20261117-03`

- Official result: `reward=0.0`, `business_pass=false`, termination `user_stop`; duration `1048.719` seconds.
- MAIN model calls: 47 requests and 47 responses; maximum request-to-response interval `24.449` seconds. No MAIN timeout occurred.
- All three business outcomes completed in the safe order: `$2,500` CLI approved (`$5,000` to `$7,500`), CloudSync dispute filed, then one expedited replacement card ordered. The customer ended with `###STOP###` after acknowledging all three outcomes.
- The previous missing-status and multiple-`in_progress` failures did not recur. Two other Todo failures remained: an appended item omitted required `content`/`activeForm`, and a same-invocation append duplicated `unresolved_facts`. No `todo_modify_rejected` event was recorded. The duplicate escaped because the boundary read disk state that lagged the Todo tool's in-memory state inside the current ReAct invocation.
- Official action mismatches were reduced to two: missing `log_verification`, and dispute `card_action=keep_active` instead of the reference `cancel_and_reissue`. Expedited replacement now matched the reference. The DB comparison still failed, so official reward remains zero.

This run validates that the new status/cardinality prompt constraints changed model behavior, but the recovery mechanism is not complete. It must validate all Core-required append fields and track authoritative Todo state in memory after every successful Todo result, rather than rereading only the persisted file.
