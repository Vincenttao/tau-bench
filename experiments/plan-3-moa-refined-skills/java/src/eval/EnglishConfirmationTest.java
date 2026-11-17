package eval;

import com.moaagent.agent.discovery.*;
import com.moaagent.agent.execution.ExecutionResources;
import com.moaagent.agent.planning.*;
import com.openjiuwen.core.session.AgentSessionApi;
import com.openjiuwen.core.singleagent.interrupt.InterruptRequest;
import java.lang.reflect.*;
import java.nio.file.Path;
import java.util.*;

/** The actual planning rail must present usable English customer confirmation. */
public final class EnglishConfirmationTest {
    public static void main(String[] args) throws Exception {
        var card = new CandidateCard("cards", "Card services", "Cards", List.of(), List.of(),
                "cards", "cards", CandidateCard.Risk.HIGH, null, CandidateCard.Kind.AGENT);
        var rail = new StagePlanningRail(new CandidatePack(List.of(card)), new ExecutionResources(Path.of("unused")));
        var plan = new StagePlan();
        plan.setPhase(StagePlan.Phase.BOUND); plan.setRevision(1);
        var todo = new StagePlan.Todo();
        todo.setId("one"); todo.setKey("one"); todo.setQuery("Help select a credit card");
        todo.setRisk(CandidateCard.Risk.HIGH); todo.setBinding(card); todo.setStatus(StagePlan.Status.BOUND);
        plan.setTodos(new ArrayList<>(List.of(todo)));
        var session = (AgentSessionApi) Proxy.newProxyInstance(AgentSessionApi.class.getClassLoader(),
                new Class<?>[]{AgentSessionApi.class}, (p, m, a) -> m.getName().equals("getSessionId") ? "english-test" : null);
        var finalize = StagePlanningRail.class.getDeclaredMethod("finalizePlan", StagePlan.class, Object.class, AgentSessionApi.class);
        finalize.setAccessible(true);
        var result = (Optional<?>) finalize.invoke(rail, plan, null, session);
        String question = ((InterruptRequest) result.orElseThrow()).getMessage();
        if (!question.contains("Yes or No") || question.codePoints().anyMatch(c -> c >= 0x4e00 && c <= 0x9fff))
            throw new AssertionError("Non-English confirmation: " + question);
        if (question.contains("v1-todo") || question.contains("HIGH"))
            throw new AssertionError("Internal planning fields leaked to customer");
        finalize.invoke(rail, plan, "Yes, but change the amount", session);
        if (plan.getFormal() || plan.getPhase() != StagePlan.Phase.CONFIRMING)
            throw new AssertionError("An amended request was treated as approval");
        finalize.invoke(rail, plan, "No", session);
        if (plan.getPhase() != StagePlan.Phase.REJECTED) throw new AssertionError("No was not honored");
        plan.setPhase(StagePlan.Phase.BOUND);
        finalize.invoke(rail, plan, "Yes", session);
        if (!plan.getFormal() || todo.getStatus() != StagePlan.Status.PENDING) throw new AssertionError("Yes did not approve plan");
        var conditional = new StagePlan();
        conditional.setPhase(StagePlan.Phase.BOUND);
        var prerequisite = new StagePlan.Todo();
        prerequisite.setKey("private-check-key"); prerequisite.setQuery("Check the available balance");
        prerequisite.setBinding(card); prerequisite.setRisk(CandidateCard.Risk.HIGH);
        prerequisite.setStatus(StagePlan.Status.BOUND);
        var payment = new StagePlan.Todo();
        payment.setKey("private-pay-key"); payment.setQuery("Make the requested payment");
        payment.setBinding(card); payment.setRisk(CandidateCard.Risk.HIGH);
        payment.setStatus(StagePlan.Status.BOUND);
        payment.setDependsOn(List.of("private-check-key"));
        payment.setWhen(Map.of("condition", "the available balance is at least 80"));
        conditional.setTodos(new ArrayList<>(List.of(prerequisite, payment)));
        String conditionalQuestion = ((InterruptRequest) ((Optional<?>) finalize.invoke(rail,
                conditional, null, session)).orElseThrow()).getMessage();
        if (!conditionalQuestion.contains("only if: the available balance is at least 80")
                || !conditionalQuestion.contains("after successful completion of: Check the available balance")
                || !conditionalQuestion.contains("if uncertain, stop")
                || conditionalQuestion.contains("private-check-key"))
            throw new AssertionError("Conditional authorization changed: " + conditionalQuestion);
        System.out.println("PASS English confirmation, Yes/No, amended request rejected, dependency and condition preserved");
    }
}
