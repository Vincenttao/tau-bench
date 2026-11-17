# MAIN model timeout diagnosis

## Historical failure

In task060-global-prompt-20261117-03, main-model-11 started at 17:52:49 and failed at 17:54:49. The Java client reported HttpTimeoutException, BEFORE_FIRST_SEGMENT/header_wait, timeout 120 seconds, max_retries=0. MAIN was using non-streaming requests. No generated tool call was executed from this failed model response.

The immediately preceding successful MAIN call used 21,871 input tokens and finished in about 11.3 seconds. The failed call was a new turn with two messages. The event journal includes duplicated serialization fields (contentAsString), so journal size must not be treated as actual wire payload size. There is no context-limit response or HTTP 429/5xx evidence for the failed call.

## Live diagnostics

Raw local evidence: `../runs/model-timeout-synthetic-probe-20261117-01/results.json`.

| Probe | Request bytes | Headers / first body | Completion | Result |
|---|---:|---:|---:|---|
| Short before | 150 | 1.141 s | 1.142 s | HTTP 200 |
| Synthetic context, non-streaming | 26,408 | 3.755 / 3.756 s | 3.756 s | HTTP 200, tool_calls |
| Synthetic context, streaming | 26,407 | 2.314 / 2.315 s | 4.276 s | HTTP 200, DONE |
| Short after | 150 | 1.096 s | 1.097 s | HTTP 200 |

All requests used the configured gateway and requested deepseek-v4-flash, temperature=0, top_p=0.8, no retries. Diagnostic read timeout was 180 seconds; no request approached it. Long inputs were entirely synthetic English shelf/block planning data, sized from the historical message character count, with one synthetic planning tool. This is not a token-matched, complexity-matched, Java-client-matched or original-input replay.

Non-streaming probes returned deepseek-v4-flash-ga-260731; the streaming probe returned deepseek-v4.1-flash-1017. These are observed response identifiers, not proof of particular backend routing or model weights. Differences in backend identity, caching and generated output prevent a controlled streaming performance comparison.

## Interpretation

Confirmed: the historical client deadline expired before a usable response, and the configured zero retry budget caused immediate failure propagation. Current short and synthetic-context probes show working authentication/connectivity and successful responses. They do not reproduce the original failure and cannot rule out intermittent network faults, gateway queuing, upstream stalls, or slower generation for the original planning task.

For a non-streaming request, waiting for the first response can include queuing and the entire generation, depending on gateway buffering; it is not necessarily a pure connection delay. Increasing the deadline changes tolerance, not the underlying cause. Streaming may expose earlier progress but was not proven to resolve this failure.

Original-input replay was blocked by automatic approval review because it would retransmit customer identity fields and banking context to the external gateway. Only synthetic probes were sent. Original replay requires explicit approval; provider-side request tracing would be needed to establish the historical server-side cause. No runtime timeout, retry setting, model configuration, benchmark task or business data was modified by this diagnostic.

## Follow-up: user-authorized sanitized replay

The user subsequently authorized replacement of sensitive fields before sending. Full name, date of birth, phone, email, mailing address and account display names were consistently replaced with fictional values. Business conditions, policy text, conversation structure and all five tool schemas were retained. No returned tool call was executed.

Evidence: `../runs/model-timeout-redacted-replay-20261117-185807/`, including `sanitized-request.json`, `results.json` and the second response. The same 33,141-byte request was sent twice, sequentially, using the existing gateway and model alias. SHA-256: `8d99730a27fa7812990cbab54c8b9124965e8e0a9e45c0535255d314f67d6e5b`. The OpenAI-compatible request was reconstructed from journal role/content and tool definitions; this is not an exact capture of the original Java HTTP request. Temperature was 0, top_p was 0.8, streaming was disabled and retries were disabled. The diagnostic read timeout was 180 seconds; production settings were not changed.

| Trial | First response | Total time | Outcome |
|---|---:|---:|---|
| 1 | No response headers received | 180.550 s | HTTPX ReadTimeout |
| 2 | Headers 8.173 s; body 8.270 s | 8.272 s | HTTP 200, tool_calls |

Trial 2 returned model identifier `deepseek-v4.1-flash-1017`, with 6,933 prompt tokens (4,096 cached) and 902 completion tokens (554 reasoning tokens). Trial 1 returned no model identifier or token usage. Do not infer its backend identity or whether generation completed after the client disconnected.

The long wait was reproduced outside MOA using an independent Python HTTP client. The identical sanitized payload then succeeded quickly. Thus the payload is not invariably rejected or invariably too slow, and the reproduced symptom does not require Java Runtime or skill execution. Intermittent gateway/network/upstream behavior, backend selection and caching remain possible factors; these observations do not distinguish them or prove that the prompt is irrelevant to latency. Raising the timeout to 180 seconds did not rescue trial 1. Provider-side tracing is still required to identify the historical server-side cause.

An initial sandbox-only attempt in `../runs/model-timeout-redacted-replay-20261117-185746/` failed DNS resolution before transmission. It is excluded from model-call results. The two calls above ran with approved network access. Raw evidence is Git-ignored; only this curated report is intended for version control.

## DeepSeek official endpoint comparison

With the user-provided DeepSeek credential supplied interactively, the official `https://api.deepseek.com/models` endpoint returned `deepseek-flash` and `deepseek-v4-pro`. The credential was not written to source, configuration or evidence. `deepseek-flash` was selected because it is the closest official Flash option to the experiment's requested alias. The same sanitized MAIN request was used; only the API base and model identifier changed. No returned tool call was executed.

Evidence: `../runs/model-timeout-deepseek-direct-20261117-190935/results.json`. Requests used temperature 0, top_p 0.8, no retries and a 180-second read timeout.

| Probe | Headers | First body | Total | Result |
|---|---:|---:|---:|---|
| Short, non-streaming | 0.143 s | 0.563 s | 0.566 s | HTTP 200, stop |
| Sanitized MAIN, non-streaming 1 | 0.153 s | 8.554 s | 8.554 s | HTTP 200, tool_calls |
| Sanitized MAIN, non-streaming 2 | 0.155 s | 16.083 s | 16.084 s | HTTP 200, tool_calls |
| Sanitized MAIN, streaming | 0.127 s | 0.133 s | 11.718 s | HTTP 200, DONE, tool_calls |

The streaming response contained 2,019 SSE events and 379 tool-call argument deltas. Concatenating those deltas produced 1,765 characters of valid JSON for one `stage_plan` call. This verifies the response shape at the OpenAI-compatible protocol boundary; it does not yet verify the complete Java MAIN execution path.

No timeout occurred in these four official-endpoint probes. This is evidence that the sanitized MAIN payload and tool schema can complete through the official endpoint. It is not yet evidence of a model-version effect: the prior gateway's successful calls also reported a V4.1 Flash backend identifier, while the timed-out calls returned no identifier. The comparison changes endpoint, account/routing and advertised model name together. A controlled Java MAIN run is required before changing the experiment default.
