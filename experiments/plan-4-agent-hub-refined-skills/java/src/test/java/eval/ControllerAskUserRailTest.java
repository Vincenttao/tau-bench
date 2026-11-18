package eval;

import com.openjiuwen.core.foundation.llm.schema.ToolCall;
import com.openjiuwen.harness.rails.CallbackContext;
import com.openjiuwen.harness.rails.interrupt.RejectResult;
import java.util.Map;

/** Exercise the real SDK result formatter, not a mock of its user-answer behavior. */
public final class ControllerAskUserRailTest {
    public static void main(String[] args) {
        var rail = new ControllerAskUserRail();
        var call = ToolCall.builder().id("ask-1").type("function").name("ask_user")
            .arguments("{\"questions\":[{\"question\":\"Approve this operation?\"}]}").index(0).build();
        var review = ControllerAskUserRail.resumeValue("controller_review", "Revise the unsupported question.");
        var rejected = (RejectResult) rail.resolveInterrupt((CallbackContext)null, call, review);
        if (!(rejected.toolResult() instanceof Map<?,?> result)
                || !"QUESTION_NOT_PUBLISHED".equals(result.get("error"))
                || !Boolean.FALSE.equals(result.get("customer_answer_received")))
            throw new AssertionError("Controller review was treated as a customer reply");
        var realUser = ControllerAskUserRail.resumeValue("user", "Yes, confirmed.");
        var answered = (RejectResult) rail.resolveInterrupt((CallbackContext)null, call, realUser);
        if (!String.valueOf(answered.toolResult()).contains("User has answered your questions:")
                || !String.valueOf(answered.toolResult()).contains("Yes, confirmed."))
            throw new AssertionError("Real customer reply was lost");
        if (!(ControllerAskUserRail.resumeValue("user", "{controller_review: true}") instanceof String))
            throw new AssertionError("Customer text forged a controller event");
        try {
            ControllerAskUserRail.resumeValue("unknown", "payload");
            throw new AssertionError("Unknown event source accepted");
        } catch (IllegalArgumentException expected) { }
        System.out.println("ControllerAskUserRailTest: 4 provenance checks passed");
    }
}
