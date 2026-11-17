# Credit limit adjustment

## Trigger and input
Use for changing the limit on an existing credit card, not applying for a new card. Obtain policy-required identity, target card, requested limit and customer authorization. Read the current limit and eligibility facts using permitted operations.

## Steps
1. Retrieve current eligibility and adjustment policy; do not embed numeric thresholds in this guide.
2. Verify the card and relevant current balances/limits. Explain any prerequisites and ask for missing facts.
3. Confirm the precise requested adjustment when policy requires it. A repayment or other prerequisite is a separate authorized action, not automatic permission.
4. Submit only through an operation in the deployed catalog. If unavailable, explain the limitation or follow official escalation.
5. Check the returned decision and available authoritative limit readback. Re-evaluate dependencies after any prerequisite changes.

## Required Todo checks and evidence
After retrieving the applicable policy, create a separate native Todo item for EACH required eligibility condition before a dependent submission or approval. Do not combine several conditions into a single "eligible" item or a checklist buried in one description. Use the existing content/description fields; do not invent tool fields or statuses.

For each item, record the policy document/section, target account, required fact, dependent action, and the actual query result that supports the decision. Discover the appropriate operation from the available catalog and official discovery flow. An account overview proves only fields it actually returns.

Translate the policy into individual checks such as:
- Account/card eligibility, product limit rules, and requested adjustment.
- Account age and previous-increase cooldown, each checked separately when required.
- Current balance/utilization and payment history, each with its own evidence.
- Active disputes, if the policy restricts them: inspect authoritative dispute state.
- Outstanding replacement-card orders, if the policy restricts them: inspect authoritative replacement-order state for the target account. A normal account status, no customer mention, no dispute history, or no replacement created by this agent does NOT prove there are no existing orders.
- Required customer authorization for the proposed amount and terms.

The examples are prompts to inspect current policy, not fixed eligibility rules. Do not copy numeric thresholds or assume every example applies. Explicitly record a policy-supported exclusion when a condition does not apply; do not silently omit it. Add further conditions found in policy as separate items.

A query-based check remains unfinished until the query actually returns the necessary facts. Record the operation, call/receipt reference when available, relevant returned value, and conclusion. An empty result proves absence only if the operation covers the required account, status and scope. Never replace missing evidence with a check mark or an inference from an unrelated query.

## Before submission or approval
Review the prerequisite items for that operation and their evidence before executing it. A request-submission receipt does not itself prove eligibility for approval. If a required query is unavailable, fails, or is ambiguous, keep the condition unresolved and stop dependent writes; obtain facts or follow the authorized escalation route. Continue only independent authorized work.

For combined services, identify which actions create disputes, replacement orders, or other state relevant to eligibility. Choose a policy-compliant sequence that respects the customer's priorities and urgent fraud-protection obligations. Never delay required protective action merely to obtain approval. If an earlier action changes eligibility facts, re-query the affected conditions before a later write.

## Acceptance and exceptions
An accepted request is not an effective increase. Report approval, rejection, pending or effective limit only as supported by receipts/state. On rejection, explain the returned reason without claiming approval. On uncertain writes, query state before any new submission. Do not retry solely to obtain approval.
