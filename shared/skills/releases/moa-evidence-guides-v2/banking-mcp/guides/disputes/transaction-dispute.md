# Card dispute handling

Apply this guide when a customer asks to dispute one or more card transactions. Read this guide on demand through banking-mcp; this guide is not a separately executable Skill ID. Use invoke_skill with skill_id=banking-mcp for all operations. Read the deployed operation catalog. Do not guess operation names, parameters, or hidden capabilities.

## Workflow
1. Verify the customer under bank policy before accessing protected records.
2. Make a complete list of requested transactions. Record card, amount, date, reason, merchant-contact status, requested resolution, and required evidence. Ask about missing facts.
3. Read the applicable policy and customer dispute history before deciding eligibility or provisional credit. Keep per-item eligibility separate from limits across the whole request or policy period.
4. For count limits, calculate `remaining = maximum allowed - qualifying prior uses`. Allocate no more than the remaining capacity. Use only policy and customer-stated priorities to select items. If history or policy is unclear, ask or escalate.
5. Before writing, review the full proposed submission list against transaction evidence, policy, customer request, and aggregate limits. Clarify material choices when policy requires it.
6. Submit using the official operation contract. Do not retry a write after an uncertain transport result; read official state first.
7. Use available authorized reads to compare submitted records with the proposal. If no readback exists, retain the authoritative submission result and explicitly state any verification limitation. Report partial completion and unresolved items. Complete Todo only after outcomes are verified or remaining work is handed off.

## Provisional credit
Eligibility and allocation are separate decisions. A reason may qualify individually while a task-wide or period-wide cap limits how many items receive credit. Count qualifying prior credits, calculate remaining capacity, then allocate within that limit. Never set a grant flag based only on single-transaction eligibility.

## Required Todo checks and evidence
After reading the applicable policy, create independent Todo checks for identity/authorization, each transaction's identity and issue, each required eligibility condition, provisional-credit eligibility, any aggregate capacity, the authorized submission, and receipt/state verification. Create only policy-applicable checks, and add newly discovered requirements before dependent actions. Do not collapse these checks into one "handle dispute" task.

Use native Todo content/description fields to record the policy source, affected transaction/account, required evidence, dependent action, and observed result. For transaction facts, retain the authoritative transaction query; for history-based restrictions or remaining capacity, actually query the relevant history. A customer description does not replace required bank records. A current transaction or account overview does not establish the absence of prior disputes or credits.

Complete a check only when its required evidence supports the conclusion. Record the operation, available call/receipt reference and relevant result. Distinguish "not queried", "query failed", "no matching records" and "records returned". Only a successful query with the correct scope supports an absence claim. For aggregate limits, record the policy maximum, qualifying prior uses and remaining capacity, then reconcile all proposed transactions against that capacity.

Before filing, inspect the prerequisite Todo items and verify the proposed reason, amount, remedy, credit flag and card action against evidence and customer authorization. Missing facts or unsupported eligibility stop the dependent submission; query, clarify or escalate rather than mark the item completed. Continue independent authorized items and report partial completion accurately.

In combined requests, filing a dispute or cancelling a card may change eligibility for another service. Consult its guide, identify the dependency before writing, and recheck affected pending items after the state changes. Respect fraud-protection requirements and customer priorities; do not reorder actions merely to make another operation pass.

## Resolution amount
Match the resolution to the issue and amount. For an overcharge with posted and expected amounts, calculate the difference and clarify the requested amount when needed. Do not silently turn a partial overcharge into a full-transaction refund.

Treat tool results as evidence, check success and textual errors, and verify every write. Do not include benchmark answers, customer data, expected scores, or fixed transaction priorities in this Skill.

## Completion and exception conditions
Maintain an item-level reconciliation of the customer request, policy evidence, authorized disposition and observed receipt/status. A submitted dispute is not a resolved dispute or settled refund. Provisional credit is not a final refund. Report these stages accurately.

If one item is rejected or uncertain, continue other items only when they are independent and still authorized; identify partial completion explicitly. Missing policy or history prevents a supported eligibility decision. An escalation receipt confirms referral only. Do not mark the underlying dispute resolved without authoritative evidence.

When reviewing a set of transactions, reconcile the set of observed transaction IDs against the items you checked. For each item examine the applicable product rate, category and merchant exceptions, the observed amount, the expected amount and the direction of any difference. Use the applicable policy to determine the next action for each discrepancy. Do not infer a one-direction rule from a few examples. Preserve unresolved items when evidence is incomplete.

Read the discovered operation's description before stating what its fields do. If a field records a requested disposition, confirm any separate execution through the operation and service authorized to perform it. Check whether a follow-up lookup covers the same type of record as the original submission before reporting that a record is missing.
