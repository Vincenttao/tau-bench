package eval;

import com.moaagent.agent.support.Json;
import com.openjiuwen.core.foundation.llm.schema.AssistantMessage;
import com.openjiuwen.core.session.AgentSessionApi;
import com.openjiuwen.core.singleagent.rail.*;
import java.lang.reflect.Proxy;
import java.nio.file.*;
import java.util.*;

public final class MainModelEvidenceTest {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("main-evidence-");
        try {
            var rail = new MainModelEvidenceRail(root);
            var input = ModelCallInputs.builder().messages(List.of(Map.of("role", "user", "content", "Compare X and Y"))).build();
            input.setTools(List.of(Map.of("name", "stage_status")));
            input.setRequestHeaders(Map.of("Authorization", "secret-not-for-trace"));
            var session = (AgentSessionApi) Proxy.newProxyInstance(AgentSessionApi.class.getClassLoader(),
                    new Class<?>[]{AgentSessionApi.class}, (p, m, a) -> m.getName().equals("getSessionId") ? "session-a" : null);
            var ctx = new AgentCallbackContext(); ctx.setSession(session); ctx.setInputs(input);
            String before = Json.write(input.getMessages());
            rail.beforeModelCall(ctx);
            input.setResponse(new AssistantMessage("Synthetic response"));
            rail.afterModelCall(ctx);
            var lines = Files.readAllLines(root.resolve("main-model-events.jsonl"));
            if (lines.size() != 2 || !Json.object(lines.get(0)).get("call_id").equals(Json.object(lines.get(1)).get("call_id")))
                throw new AssertionError("Missing input/output association");
            if (!lines.get(0).contains("Compare X and Y") || lines.toString().contains("secret-not-for-trace"))
                throw new AssertionError("Wrong capture fields");
            if (!before.equals(Json.write(input.getMessages())) || input.getRequestHeaders().size() != 1)
                throw new AssertionError("Observer mutated model inputs");
            input.setResponse(null);
            rail.beforeModelCall(ctx);
            ctx.setException(new RuntimeException("synthetic timeout"));
            rail.onModelException(ctx);
            rail.afterModelCall(ctx);
            lines = Files.readAllLines(root.resolve("main-model-events.jsonl"));
            if (lines.size() != 4 || lines.toString().contains("unmatched"))
                throw new AssertionError("Exception callback produced a phantom response");
            // Failed capture must not request retries, suppress errors, or change execution.
            var broken = new MainModelEvidenceRail(root.resolve("missing-parent"));
            broken.beforeModelCall(ctx);
            if (ctx.consumeRetryRequest() != null || ctx.hasForceFinishRequest())
                throw new AssertionError("Observer altered control flow");
            System.out.println("PASS model evidence correlation, credential exclusion, read-only failure behavior");
        } finally {
            try (var files = Files.walk(root)) {
                for (Path p : files.sorted(Comparator.reverseOrder()).toList()) Files.delete(p);
            }
        }
    }
}
