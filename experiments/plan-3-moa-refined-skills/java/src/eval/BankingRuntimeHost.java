package eval;

import com.moaagent.agent.discovery.*;
import com.moaagent.agent.support.Json;
import com.moaagent.agent.rail.MoaAgentRailProvider;
import com.openjiuwen.core.foundation.llm.Model;
import com.openjiuwen.core.foundation.llm.schema.ModelRequestConfig;
import com.openjiuwen.core.runner.Runner;
import com.openjiuwen.service.spec.spi.AgentHandler;
import com.openjiuwen.service.adapters.agentcore.ext.agentfw.JiuwenCoreAgentExtHandler;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.web.server.context.WebServerApplicationContext;
import org.springframework.context.annotation.Bean;
import java.nio.file.*;
import java.net.URI;
import java.net.http.*;
import java.util.*;

/** A separate actual Runtime process for MAIN or one banking domain. */
@SpringBootConfiguration
@EnableAutoConfiguration
public class BankingRuntimeHost {
    static Map<String,Object> init;

    @Bean
    @ConditionalOnProperty(name="banking.role", havingValue="main")
    MoaAgentRailProvider mainModelEvidence() {
        Path workspace = Path.of(String.valueOf(init.get("workspace")));
        return role -> role == MoaAgentRailProvider.Role.MAIN
                ? List.of(new MainModelEvidenceRail(workspace)) : List.of();
    }

    @Bean
    CandidatePack bankingCandidates() {
        List<CandidateCard> cards = new ArrayList<>();
        for (Object raw : (List<?>) init.get("candidates")) {
            var item = Json.object(raw);
            String id = String.valueOf(item.get("id"));
            cards.add(new CandidateCard(id, id, String.valueOf(item.get("description")),
                    List.of(), List.of(), id, id, CandidateCard.Risk.HIGH, null, CandidateCard.Kind.AGENT));
        }
        return new CandidatePack(cards);
    }

    @Bean(destroyMethod="close")
    @ConditionalOnProperty(name="banking.role", havingValue="domain")
    DeepAgentAssembly bankingDomainAssembly() throws Exception {
        var model = new Model(DeepAgentBridge.modelClientConfig(System.getenv("OPENAI_API_KEY"),
                System.getenv("OPENAI_BASE_URL"), 120), ModelRequestConfig.builder()
                .temperature(0.0).topP(1.0).modelName(String.valueOf(init.get("model"))).build());
        var domainInit = new java.util.HashMap<String, Object>(init);
        domainInit.put("domain_policy", BankingPrompts.domainPolicy(String.valueOf(init.get("domain_policy"))));
        var assembly = new DeepAgentAssembly(domainInit, model);
        assembly.agent.deepConfig().setCompletionTimeout(1200.0);
        return assembly;
    }

    @Bean
    @ConditionalOnProperty(name="banking.role", havingValue="domain")
    AgentHandler bankingDomainHandler(DeepAgentAssembly assembly) {
        return new JiuwenCoreAgentExtHandler(assembly.agent);
    }

    public static void main(String[] args) throws Exception {
        var framedOutput = DeepAgentBridge.OUT;
        System.setOut(System.err);
        try {
            init = DeepAgentBridge.read();
            String role = String.valueOf(init.get("role"));
            if (!Set.of("main", "domain").contains(role)) throw new IllegalArgumentException("Unknown Runtime role");
            String id = String.valueOf(init.get("agent_id"));
            Path workspace = Path.of(String.valueOf(init.get("workspace"))).toAbsolutePath();
            Files.createDirectories(workspace);
            var defaults = new LinkedHashMap<String,Object>();
            defaults.put("banking.role", role);
            defaults.put("server.address", "127.0.0.1"); defaults.put("server.port", 0);
            defaults.put("spring.application.name", id); defaults.put("openjiuwen.service.agent-id", id);
            defaults.put("openjiuwen.service.agentcore.request-context.enabled", true);
            defaults.put("openjiuwen.service.agentcore.response-metadata.enabled", true);
            defaults.put("openjiuwen.service.external.sandbox.enabled", false);
            defaults.put("openjiuwen.service.llm.provider", "OpenAI");
            defaults.put("openjiuwen.service.llm.api-key", System.getenv().getOrDefault("OPENAI_API_KEY", "bootstrap-no-model"));
            defaults.put("openjiuwen.service.llm.api-base", System.getenv().getOrDefault("OPENAI_BASE_URL", "https://example.invalid/v1"));
            defaults.put("openjiuwen.service.llm.model-name", init.get("model"));
            defaults.put("openjiuwen.service.llm.temperature", 0.0);
            defaults.put("openjiuwen.service.llm.timeout", "120s");
            defaults.put("moa.skill-agent.enabled", false);
            defaults.put("moa.orchestration.workspace", workspace.toString());
            defaults.put("moa.orchestration.analysis-timeout", "120s");
            defaults.put("moa.orchestration.arbitration-timeout", "120s");
            if (role.equals("domain")) {
                defaults.put("spring.autoconfigure.exclude", "com.moaagent.runtime.orchestration.MoaRuntimeAutoConfiguration");
            } else {
                Path prompt = workspace.resolve("main-prompt.md");
                String content = BankingPrompts.mainPrompt(String.valueOf(init.get("domain_policy")));
                Files.writeString(prompt, content);
                Files.writeString(workspace.resolve("main-prompt-meta.json"), Json.write(Map.of(
                        "version", BankingPrompts.VERSION, "sha256", ObservedToolContext.sha256(content),
                        "model_evidence", "main-model-events.jsonl", "capture", "read-only ModelCallInputs boundary")));
                defaults.put("moa.prompts.orchestration", prompt.toUri().toString());
            }
            int index = 0;
            for (Object raw : (List<?>) init.get("candidates")) {
                var item = Json.object(raw);
                String prefix = "openjiuwen.service.a2a.remote-agents[" + index++ + "].";
                defaults.put(prefix + "name", item.get("id"));
                defaults.put(prefix + "url", item.get("url"));
                defaults.put(prefix + "streaming", true);
                // Non-streaming A2A waits for a whole domain turn, not one model call.
                defaults.put(prefix + "timeout-seconds", init.getOrDefault("remote_timeout_seconds", 1260));
            }
            var app = new SpringApplication(BankingRuntimeHost.class);
            app.addInitializers(context -> context.getEnvironment().getPropertySources().addFirst(
                    new org.springframework.core.env.MapPropertySource("banking-experiment", defaults)));
            try (var context = app.run()) {
                var handler = context.getBean(AgentHandler.class);
                int port = ((WebServerApplicationContext) context).getWebServer().getPort();
                String url = "http://127.0.0.1:" + port;
                var card = HttpClient.newHttpClient().send(HttpRequest.newBuilder(
                        URI.create(url + "/.well-known/agent-card.json")).GET().build(), HttpResponse.BodyHandlers.ofString());
                if (card.statusCode() != 200) throw new IllegalStateException("Agent card unavailable");
                DeepAgentBridge.emit(Map.of("type", "ready", "role", role, "agent_id", id,
                        "pid", ProcessHandle.current().pid(), "url", url, "handler", handler.getClass().getName(),
                        "agent_card", Json.object(card.body())));
                if (!"close".equals(DeepAgentBridge.read().get("type"))) throw new IllegalArgumentException("Expected close");
            }
        } catch (Throwable error) {
            error.printStackTrace(System.err);
            DeepAgentBridge.emit(Map.of("type", "error", "error", error.toString()));
            System.exit(1);
        } finally { Runner.stop(); }
    }
}
