package eval;

import java.util.List;
import java.util.Map;

/** Executor resource bound; never a business completion predicate. */
public final class TodoLimit {
    private TodoLimit() {}
    public static void check(String tool, Map<String,Object> arguments) {
        if ("todo_create".equals(tool) && arguments.get("tasks") instanceof List<?> tasks && tasks.size() > 32)
            throw new IllegalArgumentException("Todo limit exceeded: at most 32 items");
    }
}
