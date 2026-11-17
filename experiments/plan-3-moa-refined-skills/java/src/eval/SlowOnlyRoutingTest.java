package eval;

import com.moaagent.agent.discovery.*;
import com.moaagent.agent.routing.*;
import com.moaagent.agent.routing.cardinality.TaskCardinality;
import com.openjiuwen.core.session.AgentSessionApi;
import java.lang.reflect.Proxy;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Exercises the actual MOA router, including its pre-policy bypasses. */
public final class SlowOnlyRoutingTest {
    public static void main(String[] args) {
        var card = new CandidateCard("card-application-agent", "Cards", "Card applications", List.of(),
                List.of(), "cards", "cards", CandidateCard.Risk.HIGH, null, CandidateCard.Kind.AGENT);
        var pack = new CandidatePack(List.of(card));
        var states = new HashMap<String, Object>();
        var envs = new HashMap<String, Object>();
        var session = (AgentSessionApi) Proxy.newProxyInstance(AgentSessionApi.class.getClassLoader(),
                new Class<?>[]{AgentSessionApi.class}, (proxy, method, values) -> switch (method.getName()) {
                    case "getState" -> states.get(values[0]);
                    case "getEnvs" -> envs;
                    case "getSessionId" -> "slow-only-test";
                    case "updateState" -> { states.putAll((Map<String, Object>) values[0]); yield null; }
                    default -> null;
                });
        var fastServiceCalls = new AtomicInteger();
        try (var router = new IntentRouter((q, s) -> { fastServiceCalls.incrementAndGet(); return List.of(card); },
                (q, s) -> { fastServiceCalls.incrementAndGet(); return TaskCardinality.SINGLE; },
                pack, Duration.ofSeconds(1))) {
            requireSlow(router.route("Apply for a credit card", "", session), "normal");
            requireSlow(router.route("Apply for a credit card", "cards", session), "explicit");
            envs.put("runtime.request_context", Map.of("metadata", Map.of("moa.intent_handoff", Map.of(
                    "mode", "TARGET", "query", "Apply for a credit card", "targetIntent", "cards",
                    "candidateCapabilityIds", List.of(), "serviceLeadOut", Map.of()))));
            requireSlow(router.route("Apply for a credit card", "", session), "TARGET");
            if (fastServiceCalls.get() != 0) throw new AssertionError("Fast intent/cardinality services called");
        }
        System.out.println("PASS real MOA slow routing: ordinary, explicit, TARGET; fast_service_calls=0");
    }

    static void requireSlow(IntentRouter.Decision decision, String path) {
        if (decision.action() != IntentRouter.Action.SLOW)
            throw new AssertionError(path + " bypassed slow planning: " + decision.action());
    }
}
