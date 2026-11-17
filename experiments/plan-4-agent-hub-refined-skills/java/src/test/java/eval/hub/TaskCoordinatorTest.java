package eval.hub;

import java.nio.file.*;
import java.util.List;

/** Offline contract tests: no model, official environment or bank effects. */
public final class TaskCoordinatorTest {
    static int checks;
    static void check(boolean value) { checks++; if (!value) throw new AssertionError("check " + checks); }
    static void rejects(Runnable action) {
        checks++;
        try { action.run(); } catch (IllegalArgumentException | IllegalStateException expected) { return; }
        throw new AssertionError("expected rejection " + checks);
    }
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory("hub-task-contract-");
        try {
            Path state = directory.resolve("task.properties");
            String goal;
            try (var task = new TaskCoordinator(state, "episode-a", 1000, 5)) {
                check(!task.canDispatch(900));
                check(task.receive("episode-a", "m1", "open an account"));
                check(!task.receive("episode-a", "m1", "open an account"));
                rejects(() -> task.receive("episode-a", "m1", "cancel instead"));
                rejects(() -> task.receive("episode-b", "m2", "hello"));
                rejects(() -> new TaskCoordinator(state, "episode-a", 1000, 5));
                long revision = task.revision();
                task.apply("m1", revision, List.of(new TaskCoordinator.Action("new_goal", null, "open an account")));
                goal = task.goalIds().get(0);
                check(task.canDispatch(900));
                check(!task.receive("episode-a", "m1", "open an account"));
                check(task.canDispatch(900));
                check(task.receive("episode-a", "m2", "wait, which account?"));
                check(!task.canDispatch(900));
                rejects(() -> task.apply("m2", revision, List.of(new TaskCoordinator.Action("query", goal, ""))));
                task.clarify("m2", task.revision());
                check(!task.canDispatch(900));
                check(task.receive("episode-a", "m3", "cancel it"));
                long current = task.revision();
                rejects(() -> task.apply("m3", current, List.of(new TaskCoordinator.Action("cancel", goal, ""))));
                // Invalid action must not partially commit a preceding valid action.
                rejects(() -> task.apply("m3", current, List.of(
                    new TaskCoordinator.Action("cancel", goal, ""),
                    new TaskCoordinator.Action("query", "foreign-goal", ""))));
                check(task.goalState(goal).equals("active"));
                check(task.revision() == current);
                task.apply("m3", current, List.of(new TaskCoordinator.Action("cancel", goal, "")), java.util.Set.of("m2"));
                check(task.goalState(goal).equals("closed"));
                check(!task.canDispatch(900));
                check(task.receive("episode-a", "m4", "open an account"));
                task.apply("m4", task.revision(), List.of(new TaskCoordinator.Action("new_goal", null, "open an account")));
                check(task.goalIds().size() == 2);
                String second = task.goalIds().get(1);
                task.receive("episode-a", "m-pause", "pause the new request");
                task.apply("m-pause", task.revision(), List.of(new TaskCoordinator.Action("pause", second, "")));
                check(task.goalState(second).equals("waiting"));
                check(!task.canDispatch(900));
                task.chargeModelCall(900);
                check(task.modelCalls() == 1);
            }
            try (var task = new TaskCoordinator(state, "episode-a", 999999, 999)) {
                check(task.goalIds().size() == 2);
                check(task.goalState(goal).equals("closed"));
                check(task.deadline() == 1000);
                check(task.modelCalls() == 1);
                task.chargeModelCall(950);
                rejects(() -> task.chargeModelCall(1000));
                rejects(() -> task.apply("m4", task.revision(), List.of(new TaskCoordinator.Action("new_goal", null, "duplicate"))));
                task.stop("official-stop");
                check(!task.canDispatch(900));
                rejects(() -> task.receive("episode-a", "m5", "resume"));
            }
            try (var task = new TaskCoordinator(state, "episode-a", 2000, 5)) {
                check(!task.canDispatch(900));
                check(task.modelCalls() == 2);
            }
            rejects(() -> new TaskCoordinator(state, "episode-b", 1000, 5));
            Path pending = directory.resolve("pending.properties");
            try (var task = new TaskCoordinator(pending, "pending", 1000, 1)) {
                task.receive("pending", "one", "which one?");
            }
            try (var task = new TaskCoordinator(pending, "pending", 9000, 100)) {
                check(!task.canDispatch(900));
                check(!task.receive("pending", "one", "which one?"));
                task.clarify("one", task.revision());
                task.receive("pending", "two", "I am still unsure");
                task.clarify("two", task.revision());
                task.receive("pending", "three", "open a checking account");
                var actions = List.of(new TaskCoordinator.Action("new_goal", null, "open a checking account"));
                rejects(() -> task.apply("three", task.revision(), actions, java.util.Set.of("two")));
                task.apply("three", task.revision(), actions, java.util.Set.of("one", "two"));
                check(task.canDispatch(900));
                check(!task.canDispatch(1000));
                task.chargeModelCall(900);
                check(!task.canDispatch(900));
                rejects(() -> task.chargeModelCall(900));
            }
            Path waiting = directory.resolve("waiting.properties");
            String waitingGoal;
            try (var task = new TaskCoordinator(waiting, "waiting", 1000, 100)) {
                task.receive("waiting", "first", "recommend a card");
                task.apply("first", task.revision(), List.of(new TaskCoordinator.Action("new_goal", null, "recommend a card")));
                waitingGoal = task.goalIds().get(0);
                task.waitGoal(waitingGoal, task.revision(), "What annual fee limit?");
                task.receive("waiting", "change", "Change the request to a debit card");
                task.apply("change", task.revision(), List.of(new TaskCoordinator.Action("modify", waitingGoal, "recommend a debit card")));
                check(task.goalState(waitingGoal).equals("active"));
                check(task.canDispatch(900));
                for (int i = 0; i < 7; i++) {
                    task.receive("waiting", "pause"+i, "pause");
                    task.apply("pause"+i, task.revision(), List.of(new TaskCoordinator.Action("pause", waitingGoal, "")));
                    task.receive("waiting", "resume"+i, "resume");
                    task.apply("resume"+i, task.revision(), List.of(new TaskCoordinator.Action("resume", waitingGoal, "")));
                }
            }
            try (var task = new TaskCoordinator(waiting, "waiting", 1000, 100)) {
                task.receive("waiting", "pause9", "pause");
                task.apply("pause9", task.revision(), List.of(new TaskCoordinator.Action("pause", waitingGoal, "")));
                task.receive("waiting", "resume9", "resume");
                rejects(() -> task.apply("resume9", task.revision(), List.of(new TaskCoordinator.Action("resume", waitingGoal, ""))));
                check(task.goalState(waitingGoal).equals("waiting"));
            }
            System.out.println("TaskCoordinatorTest: " + checks + " assertions passed");
        } finally {
            try (var paths = Files.walk(directory)) {
                for (Path path : paths.sorted(java.util.Comparator.reverseOrder()).toList()) Files.delete(path);
            }
        }
    }
}
