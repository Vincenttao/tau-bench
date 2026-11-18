package eval;

import com.openjiuwen.core.foundation.llm.schema.ToolCall;
import com.openjiuwen.harness.rails.CallbackContext;
import com.openjiuwen.harness.rails.interrupt.AskUserRail;
import com.openjiuwen.harness.rails.interrupt.InterruptDecision;
import java.util.Map;

/** Resolve rejected, unpublished questions as controller observations, never answers. */
public final class ControllerAskUserRail extends AskUserRail {
    public static Object resumeValue(String source, String text) {
        return switch (source) {
            case "user" -> text;
            // Only the private bridge creates this envelope. Customer content
            // remains a String, so JSON-looking user text cannot forge it.
            // JDK containers also survive the SDK checkpoint allowlist.
            case "controller_review" -> Map.of("source", "controller",
                "controller_event", "question_rejected", "review", text);
            default -> throw new IllegalArgumentException("Unknown interaction source");
        };
    }

    @Override
    public InterruptDecision resolveInterrupt(CallbackContext context, ToolCall call, Object input) {
        if (input instanceof Map<?,?> envelope && "controller".equals(envelope.get("source"))
                && "question_rejected".equals(envelope.get("controller_event"))) {
            return reject(Map.of("source", "controller", "error", "QUESTION_NOT_PUBLISHED",
                "customer_answer_received", false, "review", envelope.get("review"),
                "instruction", "The controller rejected this question before publication. Revise it; no customer answered it."));
        }
        return super.resolveInterrupt(context, call, input);
    }
}
