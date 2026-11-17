package eval;

import java.util.Collections;
import java.util.Map;

public final class TodoLimitTest {
    public static void main(String[] args) {
        TodoLimit.check("todo_create", Map.of("tasks", Collections.nCopies(32, Map.of("content", "fixture"))));
        try {
            TodoLimit.check("todo_create", Map.of("tasks", Collections.nCopies(33, Map.of("content", "fixture"))));
            throw new AssertionError("Excess Todo items admitted");
        } catch (IllegalArgumentException expected) { }
        TodoLimit.check("todo_modify", Map.of());
        System.out.println("TodoLimitTest: passed");
    }
}
