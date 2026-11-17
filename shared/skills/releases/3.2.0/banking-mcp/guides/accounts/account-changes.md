# Account and card changes

Use for opening, closing, replacing, freezing, transferring, changing limits or updating accounts/cards. Read the dispute guide too when a change follows a contested transaction or fraud report.

## Required information
Identify the target customer, accounts/cards, requested changes and policy-required authorization. Establish relevant current states and constraints using permitted reads. Clarify amounts, destinations and material choices before a write; never infer permission from a different earlier operation.

## Procedure
1. Verify identity and permissions under bank policy before protected access or changes.
2. Read current account/card state and applicable policies. Determine prerequisites and dependencies: account eligibility, available balance, holds, pending items, fees, limits and required predecessor operations where relevant.
3. Prepare a sequence that preserves the prerequisites of later actions. Explain material choices and consequences; obtain any policy-required confirmation for the exact proposed change.
4. Execute only authorized catalog operations. Stop dependent writes when a prerequisite fails or becomes uncertain. Do not compensate, reverse or retry a write automatically without policy support and authorization.
5. Inspect authoritative receipts and available readback. Compare the affected states and amounts with the authorized request. For a combined goal, reconcile every requested change before closing the task.

## Required Todo checks and evidence
Translate applicable policy into separate native Todo items for authorization, each required current-state or eligibility check, the proposed change, and outcome verification. Each condition that can block a write needs its own item, not a check mark inside a broad "change account" description. Use existing content/description fields for the source, target account/card, required fact, dependent action and observed evidence.

For card replacement, inspect the current card/account and each policy-required condition concerning existing orders, card status, replacement reason, shipping destination, delivery choice and fees. Confirm material choices as policy requires. Discover supported queries and writes from the actual catalog; do not guess hidden tools or assume every example is mandatory.

For any absence claim required by policy, obtain a successful query covering the relevant object and status. A healthy account, an unrelated query, customer silence, or the fact that this agent has not created an order does not establish the absence of existing orders, holds or pending changes. A failed or incomplete query leaves the check unfinished.

Before writing, review the applicable Todo checks and the actual results supporting them. Record the operation and call/receipt reference when available. Stop dependent writes when a prerequisite is unverified or fails; query, clarify or escalate. Do not mark the condition satisfied just because the write tool accepts the request.

For combined services, record how each proposed change affects pending tasks before choosing the order. A newly opened dispute, replacement order, closure or balance change can invalidate a previous check. Read the specific service guides, respect urgent protective obligations and customer authorization, and refresh affected evidence before the next dependent write. Do not reuse pre-change facts as proof of the new state.

After writing, distinguish an accepted request from the effective change. An order receipt supports "replacement ordered", not "card delivered"; a handoff supports "referred", not "business completed". Preserve unresolved checks and report their blockers even when another task succeeds.

## Completion and exception conditions
Report an individual change as completed only when a receipt or authoritative state confirms it. Distinguish requested, submitted, pending approval, effective and rejected states. Do not treat an accepted request as an effective account change.

A composite request is complete only when all requested outcomes are verified, or the customer has explicitly agreed to a narrower goal. Otherwise identify completed, rejected, uncertain and outstanding items separately. Escalation is a handoff, not proof of completion. For an uncertain write, reconcile state before any new submission; if no verification operation exists, retain the receipt and state that limitation.
