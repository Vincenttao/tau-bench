package eval.hub;

import java.nio.file.Files;
import java.util.List;

/** Offline-only entropy injection; production allocation remains random. */
public final class ReplayIdentityTest {
    public static void main(String[] args) throws Exception {
        var directory = Files.createTempDirectory("hub-replay-identities-");
        var path = directory.resolve("task.properties");
        var ids = List.of("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222");
        try {
            try (var task = new TaskCoordinator(path, "episode", 1000, 64)) {
                task.useReplayGoalIds(ids);
                task.receive("episode", "m", "two goals");
                task.apply("m", task.revision(), List.of(new TaskCoordinator.Action("new_goal", null, "A"),
                    new TaskCoordinator.Action("new_goal", null, "B")));
                if (!task.goalIds().equals(ids)) throw new AssertionError("Replay identities changed");
            }
            try (var task = new TaskCoordinator(path, "episode", 9999, 999)) {
                task.useReplayGoalIds(ids);
                task.receive("episode", "more", "new goal");
                try {
                    task.apply("more", task.revision(), List.of(new TaskCoordinator.Action("new_goal", null, "C")));
                    throw new AssertionError("Replay silently allocated an unrecorded identity");
                } catch (IllegalStateException expected) { }
                if (task.deadline() != 1000 || !task.goalIds().equals(ids)) throw new AssertionError("Replay reset state");
            }
            System.out.println("ReplayIdentityTest: passed");
        } finally {
            try (var paths = Files.walk(directory)) {
                for (var item : paths.sorted(java.util.Comparator.reverseOrder()).toList()) Files.delete(item);
            }
        }
    }
}
