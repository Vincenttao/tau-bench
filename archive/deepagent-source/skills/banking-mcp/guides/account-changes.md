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

## Completion and exception conditions
Report an individual change as completed only when a receipt or authoritative state confirms it. Distinguish requested, submitted, pending approval, effective and rejected states. Do not treat an accepted request as an effective account change.

A composite request is complete only when all requested outcomes are verified, or the customer has explicitly agreed to a narrower goal. Otherwise identify completed, rejected, uncertain and outstanding items separately. Escalation is a handoff, not proof of completion. For an uncertain write, reconcile state before any new submission; if no verification operation exists, retain the receipt and state that limitation.
