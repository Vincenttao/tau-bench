# Funds transfer

## Trigger and required information
Use when the customer requests a funds transfer, including transfer before account closure. Obtain policy-required identity, source, destination, amount, currency and authorization. Clarify material choices, fees and timing using available policy. Never substitute a destination or infer approval from a balance query.

## Steps
1. Read relevant account states, transferable funds and policy restrictions using authorized tools. Check any required holds, limits and recipient conditions from actual evidence.
2. Explain the precise proposed transfer and obtain policy-required authorization. Do not expose or request unnecessary account data.
3. Verify the operation exists in the deployed catalog and use its exact schema. Unsupported transfer types require an explicit limitation or authorized referral.
4. Submit once; use the receipt and permitted status/balance queries to establish the outcome. An uncertain result blocks dependent closure or follow-on writes until reconciled.

## Acceptance and exceptions
Distinguish received, pending, rejected and completed. Completion requires the authoritative transfer result or available state confirmation; never infer settlement from an HTTP success. Preserve a receipt/reference if provided. Do not fabricate an identifier when absent. For a combined request, transfer completion does not complete account closure. No blind retries, automatic reversals or unrequested compensation.

Clarify whether the customer authorized execution or only a status check. Receipt of a handoff confirms only that handoff. Verify the observed payment record or payment operation reply before reporting submission, settlement or remaining dependencies. A claimed customer action with no visible receipt remains unverified.
