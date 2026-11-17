# Full observed tool context adapter (separate experimental variant)

Run `./run.sh` with the same model environment variables as the preceding bridge.

Uses the public `NativeSkillAgent.ExecutionServices` / `ModelContextContributor` SPI. No product source, official benchmark, retrieval configuration, top_k, tool output, or evaluation criterion is changed. Arguments_json and initial-history transcript adaptations remain.

For EVERY observed official tool response:
1. Keep the complete original string, operation name, arguments, unique call ID, SHA-256 of UTF-8, and Java character count in an episode-scoped in-memory cache.
2. Return a short reference/hash/length receipt as SkillOperation data/model_data. Here success means adapter receipt storage, not business success.
3. Before each subsequent model call, append one clearly labeled tool-data/non-instruction context block containing ALL observed results chronologically as JSON. Replace a prior injected block instead of accumulating duplicates. Existing default model context contributor is retained.
4. Responses over 65536 characters are also kept in the adapter cache, not inserted into the bounded native operation result store. No truncation, pagination or summarization occurs.

The resulting context is represented as a user-role message because this is the documented projection SPI and creating unmatched provider-level tool messages would invalidate tool-call pairing. Its text explicitly identifies it as observed untrusted tool data, not user instructions. This is an adaptation in model input presentation, not native per-tool message replay.

IMPORTANT: The full text cache is an evaluation bridge responsibility, NOT native persistent checkpoint state. Process crash loses it. All full texts are re-injected and can exhaust model context/token limits in long episodes; such errors must be retained, never silently truncated. This does not demonstrate native large-result storage, cross-process recovery, Runtime hosting, or full MOA multi-agent orchestration.

Offline verification (`logs/fullcontext-selftest.log`): five real official BM25 KB results, 13944–25537 Java characters, retained byte-equivalent content verified by SHA-256; a 100000-character synthetic result verifies the >65536 path; all six retained simultaneously in ModelCallInputs; repeated projection produces no duplicate block; receipts pass actual SkillSchema validation. These tests verify model INPUT contents only, not model understanding or benchmark success. No model calls.

Actual 15-tool smoke-v2 initialization payload with assistant greeting/tool_calls:null passes init/close with loopback nonfunctional model endpoint. Model settings remain temperature=0, top_p=1, seed unset, 100 internal iterations.
