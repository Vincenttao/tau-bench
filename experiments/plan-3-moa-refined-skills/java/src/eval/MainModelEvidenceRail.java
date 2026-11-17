package eval;

import com.moaagent.agent.support.Json;
import com.openjiuwen.core.foundation.llm.schema.AssistantMessage;
import com.openjiuwen.core.singleagent.rail.*;
import java.nio.file.*;
import java.util.*;

/** Read-only MAIN model boundary capture; no headers, credentials or execution state. */
public final class MainModelEvidenceRail extends AgentRail {
    private final Path file;
    private final Map<String, String> pending = new HashMap<>();
    private long sequence;

    MainModelEvidenceRail(Path workspace) {
        file = workspace.resolve("main-model-events.jsonl");
    }

    @Override public int getPriority() { return Integer.MIN_VALUE; }

    @Override public synchronized void beforeModelCall(AgentCallbackContext ctx) {
        if (ctx.getInputs() instanceof ModelCallInputs input) {
            String session = ctx.getSession().getSessionId();
            String call = "main-model-" + (++sequence);
            pending.put(session, call);
            record(ctx, "model_request", call, Map.of(
                    "messages", input.getMessages(),
                    "tools", input.getTools() == null ? List.of() : input.getTools()));
        }
    }

    @Override public synchronized void afterModelCall(AgentCallbackContext ctx) {
        if (ctx.getInputs() instanceof ModelCallInputs input) {
            Object response = input.getResponse();
            String call = pending.remove(ctx.getSession().getSessionId());
            // The framework also invokes afterModelCall after onModelException.
            if (call == null) return;
            record(ctx, "model_response", call,
                    response instanceof AssistantMessage message ? message.modelDump()
                            : response == null ? Map.of() : response);
        }
    }

    @Override public synchronized void onModelException(AgentCallbackContext ctx) {
        record(ctx, "model_exception", pending.remove(ctx.getSession().getSessionId()),
                Map.of("exception_type", ctx.getException() == null ? "unknown"
                        : ctx.getException().getClass().getName()));
    }

    private void record(AgentCallbackContext ctx, String event, String call, Object data) {
        try {
            Files.writeString(file, Json.write(Map.of("event", event,
                    "time_ms", System.currentTimeMillis(), "session_id", ctx.getSession().getSessionId(),
                    "call_id", call == null ? "unmatched" : call, "iteration", ctx.getIteration(),
                    "data", data)) + "\n", StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception error) {
            // Observation failure must not change business execution or trigger a model retry.
            System.err.println("MAIN_MODEL_EVIDENCE_INCOMPLETE: " + error.getClass().getName());
        }
    }
}
