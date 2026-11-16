---
name: dispute-processing
description: Handle multi-transaction card disputes, policy eligibility, portfolio limits, submission, and verification.
---
# Card dispute handling

Apply this guide when a customer asks to dispute one or more card transactions. It is bundled into banking-mcp at runtime; it is not a separately executable Skill ID. Use invoke_skill with skill_id=banking-mcp for all operations. Read the deployed operation catalog. Do not guess operation names, parameters, or hidden capabilities.

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

## Resolution amount
Match the resolution to the issue and amount. For an overcharge with posted and expected amounts, calculate the difference and clarify the requested amount when needed. Do not silently turn a partial overcharge into a full-transaction refund.

Treat tool results as evidence, check success and textual errors, and verify every write. Do not include benchmark answers, customer data, expected scores, or fixed transaction priorities in this Skill.
