package eval;

import com.openjiuwen.harness.tools.TodoTools;
import com.openjiuwen.harness.schema.task.TodoItem;
import com.openjiuwen.harness.schema.task.TodoStatus;
import java.util.*;

/** Executes the real Core tools, without a model or bank operations. */
public final class TodoTransitionTest {
    public static void main(String[] args) throws Exception {
        var store = new TodoTools.TodoStore() {
            List<TodoItem> state = List.of();
            public List<TodoItem> load(Map<String,Object> kwargs) { return state; }
            public void save(List<TodoItem> todos, Map<String,Object> kwargs) { state = todos; }
        };
        var kwargs = Map.<String,Object>of("session_id", "reproduction");
        var tasks = new ArrayList<Map<String,Object>>();
        for (String id : List.of("gather_evidence", "filter_hard_reqs", "rank_candidates"))
            tasks.add(Map.of("id", id, "content", id, "activeForm", id,
                    "description", "synthetic evidence", "status", "completed"));
        new TodoTools.TodoCreateTool(store).invoke(Map.of("tasks", tasks), kwargs);
        if (store.state.get(0).getStatus() != TodoStatus.IN_PROGRESS)
            throw new AssertionError("Native creation semantics changed");
        var modify = new TodoTools.TodoModifyTool(store);
        try {
            modify.invoke(Map.of("action", "update", "todos", List.of(
                    Map.of("id", "filter_hard_reqs", "status", "completed"),
                    Map.of("id", "rank_candidates", "status", "in_progress"))), kwargs);
            throw new AssertionError("Historical failure was not reproduced");
        } catch (RuntimeException expected) {
            if (!expected.getMessage().contains("More than one task")) throw expected;
        }
        if (store.state.get(2).getStatus() != TodoStatus.PENDING)
            throw new AssertionError("Rejected update changed persisted state");
        modify.invoke(Map.of("action", "update", "todos", List.of(
                Map.of("id", "gather_evidence", "status", "completed"),
                Map.of("id", "filter_hard_reqs", "status", "completed"),
                Map.of("id", "rank_candidates", "status", "in_progress"))), kwargs);
        if (store.state.get(0).getStatus() != TodoStatus.COMPLETED ||
                store.state.get(2).getStatus() != TodoStatus.IN_PROGRESS)
            throw new AssertionError("Corrected transition failed");
        System.out.println("PASS historical Todo failure reproduced; rejected update atomic; corrected batch succeeds");
    }
}
