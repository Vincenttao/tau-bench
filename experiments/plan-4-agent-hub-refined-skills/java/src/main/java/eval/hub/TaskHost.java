package eval.hub;

import com.moaagent.agent.support.Json;
import java.io.*;
import java.nio.file.Path;
import java.util.*;

/** Private JSON-lines controller protocol, one process per episode. No model credentials. */
public final class TaskHost {
    static long number(Map<String,Object> request, String key) {
        Object value = request.get(key);
        if (!(value instanceof Number n) || n.doubleValue() != n.longValue())
            throw new IllegalArgumentException("Invalid integer: "+key);
        return n.longValue();
    }
    static String text(Map<String,Object> request, String key) {
        if (!(request.get(key) instanceof String value)) throw new IllegalArgumentException("Missing text: "+key);
        return value;
    }
    static List<String> strings(Map<String,Object> request, String key) {
        if (!(request.get(key) instanceof List<?> raw) || raw.stream().anyMatch(v -> !(v instanceof String)))
            throw new IllegalArgumentException("Invalid string list: "+key);
        return raw.stream().map(String.class::cast).toList();
    }
    public static void main(String[] args) throws Exception {
        try (var task = new TaskCoordinator(Path.of(args[0]), args[1], Long.parseLong(args[2]), Integer.parseInt(args[3]));
             var input = new BufferedReader(new InputStreamReader(System.in))) {
            String line;
            while ((line = input.readLine()) != null) {
                Map<String,Object> request = Map.of();
                var response = new LinkedHashMap<String,Object>();
                try {
                    request = Json.object(line); response.put("id", text(request,"id"));
                    String method = text(request,"method");
                    switch (method) {
                        case "status" -> response.putAll(task.snapshot(number(request,"now")));
                        case "message_status" -> response.put("status", task.messageStatus(text(request,"message")));
                        case "receive" -> response.put("fresh", task.receive(text(request,"episode"),text(request,"message"),text(request,"content")));
                        case "charge" -> task.chargeModelCall(number(request,"now"),String.valueOf(request.getOrDefault("kind","judgment")));
                        case "clarify" -> task.clarify(text(request,"message"),number(request,"revision"));
                        case "social" -> task.social(text(request,"message"),number(request,"revision"));
                        case "stop" -> task.stop(text(request,"reason"));
                        case "configure_goal" -> task.configureGoal(text(request,"goal"),number(request,"revision"),strings(request,"requirements"),text(request,"source_ref"),strings(request,"dependencies"));
                        case "record_condition" -> task.recordCondition(text(request,"goal"),number(request,"revision"),text(request,"condition"),text(request,"value"),text(request,"evidence_ref"));
                        case "accept_goal" -> task.acceptGoal(text(request,"goal"),number(request,"revision"));
                        case "wait_goal" -> task.waitGoal(text(request,"goal"),number(request,"revision"),text(request,"question"));
                        case "wait_dependency" -> task.waitDependency(text(request,"goal"),number(request,"revision"));
                        case "start_node" -> task.startNode(text(request,"node_id"),text(request,"goal"),number(request,"revision"),text(request,"kind"),text(request,"version"),text(request,"decision_ref"),number(request,"now"));
                        case "observe_node" -> task.observeNode(text(request,"node_id"),text(request,"status"));
                        case "apply" -> {
                            if (!(request.get("actions") instanceof List<?> raw)) throw new IllegalArgumentException("Missing actions");
                            var actions = new ArrayList<TaskCoordinator.Action>();
                            for (Object value : raw) {
                                var action = Json.object(value);
                                actions.add(new TaskCoordinator.Action(text(action,"kind"),
                                    action.get("goal_id") == null ? null : text(action,"goal_id"),
                                    action.get("description") == null ? "" : text(action,"description")));
                            }
                            var resolved = new HashSet<String>();
                            if (request.get("resolved") instanceof List<?> ids)
                                for (Object id : ids) { if (!(id instanceof String s)) throw new IllegalArgumentException("Invalid resolution"); resolved.add(s); }
                            task.apply(text(request,"message"),number(request,"revision"),actions,resolved);
                        }
                        default -> throw new IllegalArgumentException("Unknown method");
                    }
                    response.put("ok", true);
                } catch (RuntimeException error) {
                    response.put("ok", false); response.put("error", error.getClass().getSimpleName());
                }
                System.out.println(Json.write(response)); System.out.flush();
            }
        }
    }
}
