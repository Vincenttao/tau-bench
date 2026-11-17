package eval.hub;

import java.io.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.util.*;

/** Episode-local authoritative state. Model proposals have no direct access to this store.
 * This foundation does not grant Hub permission or execute tools.
 */
public final class TaskCoordinator implements AutoCloseable {
    public record Action(String kind, String goalId, String description) {}
    private final Path path;
    private FileChannel lockChannel;
    private FileLock lock;
    private Properties state;
    private boolean closed;

    public TaskCoordinator(Path path, String episode, long deadline, int callLimit) {
        this.path = path.toAbsolutePath();
        requireText(episode);
        if (deadline <= 0 || callLimit <= 0) throw new IllegalArgumentException("Invalid budget");
        try {
            Files.createDirectories(this.path.getParent());
            lockChannel = FileChannel.open(this.path.resolveSibling(this.path.getFileName()+".lock"),
                StandardOpenOption.CREATE, StandardOpenOption.WRITE);
            lock = lockChannel.tryLock();
            if (lock == null) throw new IllegalStateException("Task has another writer");
            if (Files.exists(this.path)) {
                state = new Properties();
                try (InputStream input = Files.newInputStream(this.path)) { state.load(input); }
                if (!"1".equals(state.getProperty("schema")) || !episode.equals(state.getProperty("episode")))
                    throw new IllegalArgumentException("State schema or episode mismatch");
                // Validate required counters before allowing any operations.
                for (String key : List.of("revision", "deadline", "callLimit", "calls", "goals")) number(key);
            } else {
                var initial = new Properties();
                initial.setProperty("schema", "1"); initial.setProperty("episode", episode);
                initial.setProperty("revision", "0"); initial.setProperty("deadline", ""+deadline);
                initial.setProperty("callLimit", ""+callLimit); initial.setProperty("calls", "0");
                initial.setProperty("goals", "0"); initial.setProperty("blocked", "true");
                initial.setProperty("stopped", "false");
                commit(initial);
            }
        } catch (IOException | RuntimeException error) {
            release();
            throw new IllegalStateException("Cannot open task state", error);
        }
    }

    private static void requireText(String text) {
        if (text == null || text.isBlank()) throw new IllegalArgumentException("Required text missing");
    }
    private static String eventKey(String message) {
        requireText(message);
        return "event."+Base64.getUrlEncoder().withoutPadding().encodeToString(message.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    private long number(String name) {
        long value = Long.parseLong(state.getProperty(name));
        if (value < 0) throw new IllegalStateException("Invalid counter: "+name);
        return value;
    }
    private void open() { if (closed) throw new IllegalStateException("Coordinator closed"); }
    private void active() {
        open();
        if (Boolean.parseBoolean(state.getProperty("stopped"))) throw new IllegalStateException("Episode stopped");
    }
    private Properties copy() { var next = new Properties(); next.putAll(state); return next; }
    private void commit(Properties next) {
        Path temporary = null;
        try {
            temporary = Files.createTempFile(path.getParent(), ".task-", ".tmp");
            try (OutputStream output = Files.newOutputStream(temporary)) { next.store(output, "Episode task schema 1"); }
            try (FileChannel channel = FileChannel.open(temporary, StandardOpenOption.WRITE)) { channel.force(true); }
            Files.move(temporary, path, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            state = next;
        } catch (IOException error) {
            closed = true; release();
            throw new IllegalStateException("State commit failed; progression refused", error);
        } finally {
            if (temporary != null) try { Files.deleteIfExists(temporary); } catch (IOException ignored) { }
        }
    }
    private void revise(Properties next) { next.setProperty("revision", ""+Math.addExact(revision(), 1)); commit(next); }

    /** Source and episode must be supplied by the trusted official adapter, never message text. */
    public synchronized boolean receive(String episode, String message, String content) {
        active(); requireText(content);
        if (!state.getProperty("episode").equals(episode)) throw new IllegalArgumentException("Foreign episode");
        String key = eventKey(message);
        if (state.containsKey(key+".content")) {
            if (!content.equals(state.getProperty(key+".content"))) throw new IllegalArgumentException("Message identity reused");
            return false;
        }
        if ("pending".equals(state.getProperty("inputStatus"))) throw new IllegalStateException("Prior input not interpreted");
        var next = copy(); next.setProperty(key+".content", content);
        next.setProperty(key+".status", "pending"); next.setProperty("latest", message);
        next.setProperty("inputStatus", "pending"); next.setProperty("blocked", "true");
        revise(next);
        return true;
    }

    private void input(String message, long revision) {
        active();
        if (revision != revision() || !message.equals(state.getProperty("latest"))
                || !"pending".equals(state.getProperty("inputStatus")))
            throw new IllegalStateException("Stale or already handled input");
    }
    public synchronized void clarify(String message, long revision) {
        input(message, revision);
        var next = copy(); next.setProperty("inputStatus", "clarify");
        next.setProperty(eventKey(message)+".status", "clarify");
        revise(next);
    }

    /** Trusted, fully validated route only. No business completion action is supported here. */
    public synchronized void apply(String message, long revision, List<Action> actions) {
        apply(message, revision, actions, Set.of());
    }

    public synchronized void apply(String message, long revision, List<Action> actions, Set<String> resolvedMessages) {
        input(message, revision);
        Set<String> unresolved = new HashSet<>();
        for (String key : state.stringPropertyNames()) {
            if (key.startsWith("event.") && key.endsWith(".status") && "clarify".equals(state.getProperty(key))) {
                String encoded = key.substring(6, key.length()-7);
                unresolved.add(new String(Base64.getUrlDecoder().decode(encoded), java.nio.charset.StandardCharsets.UTF_8));
            }
        }
        if (!unresolved.equals(resolvedMessages))
            throw new IllegalStateException("Clarification must be explicitly resolved by this route");
        if (actions == null || actions.isEmpty()) throw new IllegalArgumentException("Explicit route required");
        var next = copy(); var touched = new HashSet<String>();
        for (Action action : actions) {
            if (action == null || action.kind() == null) throw new IllegalArgumentException("Invalid action");
            if ("context".equals(action.kind())) {
                if (actions.size() != 1 || action.goalId() != null || goalIds().stream().noneMatch(id -> "active".equals(goalState(id))))
                    throw new IllegalArgumentException("Context update requires an active task and no business action");
            } else if ("new_goal".equals(action.kind())) {
                if (action.goalId() != null) throw new IllegalArgumentException("Model cannot allocate goal IDs");
                requireText(action.description());
                int count = Integer.parseInt(next.getProperty("goals"));
                if (count >= 32) throw new IllegalStateException("Goal bound reached");
                String id = UUID.randomUUID().toString();
                next.setProperty("goalIndex."+count, id); next.setProperty("goals", ""+(count+1));
                next.setProperty("goal."+id+".state", "active");
                next.setProperty("goal."+id+".description", action.description());
                next.setProperty("goal."+id+".source", message);
            } else {
                String id = action.goalId();
                if (id == null || !state.containsKey("goal."+id+".state") || !touched.add(id))
                    throw new IllegalArgumentException("Unknown or conflicting goal");
                if (!Set.of("query", "respond", "modify", "cancel", "pause", "resume").contains(action.kind()))
                    throw new IllegalArgumentException("Unsupported action");
                if (!"query".equals(action.kind()) && "closed".equals(goalState(id)))
                    throw new IllegalStateException("Closed goal cannot resume");
                if ("cancel".equals(action.kind())) {
                    next.setProperty("goal."+id+".state", "closed");
                    next.setProperty("goal."+id+".outcome", "cancelled");
                }
                if ("pause".equals(action.kind())) {
                    next.setProperty("goal."+id+".state", "waiting");
                    next.setProperty("goal."+id+".waitingKind", "paused");
                    next.remove("goal."+id+".waiting");
                }
                if ("respond".equals(action.kind()) && !state.getProperty("goal."+id+".waiting", "").isEmpty()) {
                    resumeGoal(next, id);
                }
                if ("resume".equals(action.kind())) {
                    if (!"waiting".equals(goalState(id))) throw new IllegalStateException("Only waiting goal can resume");
                    resumeGoal(next, id);
                }
                if ("modify".equals(action.kind())) {
                    requireText(action.description());
                    next.remove("goal."+id+".waitingKind");
                    next.remove("goal."+id+".dependencies");
                    if ("waiting".equals(goalState(id))) resumeGoal(next, id);
                    next.setProperty("goal."+id+".description", action.description());
                    next.setProperty("goal."+id+".source", message);
                    for (String key : new ArrayList<>(next.stringPropertyNames()))
                        if (key.startsWith("goal."+id+".condition.")) next.remove(key);
                    next.remove("goal."+id+".requirements");
                    next.remove("goal."+id+".policy");
                }
            }
        }
        next.setProperty(eventKey(message)+".status", "applied");
        for (String resolved : unresolved) next.setProperty(eventKey(resolved)+".status", "resolved");
        next.setProperty("inputStatus", "applied"); next.setProperty("blocked", "false");
        revise(next);
    }
    public synchronized long revision() { open(); return number("revision"); }
    private void resumeGoal(Properties next, String id) {
        if ("dependency".equals(next.getProperty("goal."+id+".waitingKind")))
            for (String dependency : dependencies(id))
                if (!"success".equals(next.getProperty("goal."+dependency+".outcome")))
                    throw new IllegalStateException("Dependency remains unfinished");
        if ("waiting".equals(next.getProperty("goal."+id+".state"))) {
            long resumes = Long.parseLong(next.getProperty("resumes", "0"));
            if (resumes >= 8) throw new IllegalStateException("Task resume bound reached");
            next.setProperty("resumes", ""+(resumes+1));
        }
        next.setProperty("goal."+id+".state", "active");
        next.remove("goal."+id+".waiting");
        next.remove("goal."+id+".waitingKind");
    }
    public synchronized long deadline() { open(); return number("deadline"); }
    public synchronized long modelCalls() { open(); return number("calls"); }
    private void goalRevision(String goal, long expected) {
        active(); goalState(goal);
        if (expected != revision() || "closed".equals(goalState(goal)))
            throw new IllegalStateException("Stale revision or closed goal");
    }
    private List<String> dependencies(String goal) {
        String value = state.getProperty("goal."+goal+".dependencies", "");
        return value.isEmpty() ? List.of() : List.of(value.split(","));
    }
    private void dependencyWalk(String origin, String goal, Set<String> visited, int depth) {
        if (origin.equals(goal) || depth > 4 || !visited.add(goal)) throw new IllegalArgumentException("Cyclic or excessive dependency");
        for (String parent : dependencies(goal)) dependencyWalk(origin, parent, new HashSet<>(visited), depth+1);
    }
    public synchronized void configureGoal(String goal, long expected, List<String> requirements, String source, List<String> deps) {
        goalRevision(goal, expected); requireText(source);
        if (requirements.isEmpty() || requirements.size() > 32 || new HashSet<>(requirements).size() != requirements.size())
            throw new IllegalArgumentException("Explicit bounded requirements required");
        for (String item : requirements) if (!item.matches("[A-Za-z0-9_-]{1,100}")) throw new IllegalArgumentException("Invalid requirement identity");
        for (String parent : deps) { goalState(parent); dependencyWalk(goal,parent,new HashSet<>(),1); }
        var next = copy();
        for (String key : new ArrayList<>(next.stringPropertyNames()))
            if (key.startsWith("goal."+goal+".condition.")) next.remove(key);
        next.setProperty("goal."+goal+".requirements", String.join(",", requirements));
        next.setProperty("goal."+goal+".policy", source);
        next.setProperty("goal."+goal+".dependencies", String.join(",", deps));
        revise(next);
    }
    public synchronized void recordCondition(String goal, long expected, String condition, String value, String evidence) {
        goalRevision(goal, expected); requireText(evidence);
        if (!List.of(state.getProperty("goal."+goal+".requirements", "").split(",")).contains(condition)
                || !Set.of("satisfied", "violated", "unknown").contains(value)) throw new IllegalArgumentException("Invalid condition observation");
        var next = copy(); next.setProperty("goal."+goal+".condition."+condition, value);
        next.setProperty("goal."+goal+".condition."+condition+".evidence", evidence); revise(next);
    }
    public synchronized void acceptGoal(String goal, long expected) {
        goalRevision(goal, expected);
        String requirements = state.getProperty("goal."+goal+".requirements", "");
        if (requirements.isBlank()) throw new IllegalStateException("Goal acceptance contract missing");
        for (String requirement : requirements.split(","))
            if (!"satisfied".equals(state.getProperty("goal."+goal+".condition."+requirement)))
                throw new IllegalStateException("Goal condition not established");
        for (String parent : dependencies(goal))
            if (!"success".equals(state.getProperty("goal."+parent+".outcome"))) throw new IllegalStateException("Dependency not completed");
        var next = copy(); next.setProperty("goal."+goal+".state", "closed");
        next.setProperty("goal."+goal+".outcome", "success");
        for (String candidate : goalIds()) {
            if ("waiting".equals(next.getProperty("goal."+candidate+".state"))
                    && "dependency".equals(next.getProperty("goal."+candidate+".waitingKind"))
                    && dependencies(candidate).stream().allMatch(id -> "success".equals(next.getProperty("goal."+id+".outcome")))
                    && Long.parseLong(next.getProperty("resumes", "0")) < 8)
                resumeGoal(next, candidate);
        }
        revise(next);
    }
    public synchronized void waitGoal(String goal, long expected, String question) {
        goalRevision(goal, expected); requireText(question);
        var next=copy();next.setProperty("goal."+goal+".waiting",question);
        next.setProperty("goal."+goal+".waitingKind","user");
        next.setProperty("goal."+goal+".state","waiting");revise(next);
    }
    public synchronized void waitDependency(String goal, long expected) {
        goalRevision(goal, expected);
        if (dependencies(goal).isEmpty() || dependencies(goal).stream().allMatch(id -> "success".equals(state.getProperty("goal."+id+".outcome"))))
            throw new IllegalStateException("No unfinished dependency");
        var next=copy();next.setProperty("goal."+goal+".state","waiting");
        next.setProperty("goal."+goal+".waitingKind","dependency");next.remove("goal."+goal+".waiting");revise(next);
    }
    public synchronized void startNode(String id, String goal, long expected, String kind, String version, String decision, long now) {
        goalRevision(goal, expected);
        if (!canDispatch(now) || !id.matches("[a-f0-9]{64}") || !id.equals(decision)
                || !"banking-evidence-control".equals(version)
                || !Set.of("evidence-investigation","candidate-comparison","guarded-operation","dependent-goals","receipt-reconciliation","await-user").contains(kind))
            throw new IllegalArgumentException("Unregistered or unauthorized node");
        String prefix = "node."+id+".";
        if (state.containsKey(prefix+"status")) throw new IllegalStateException("Node already started");
        var next=copy(); next.setProperty(prefix+"goal",goal);next.setProperty(prefix+"kind",kind);
        next.setProperty(prefix+"version",version);next.setProperty(prefix+"decision",decision);
        next.setProperty(prefix+"status","running"); next.setProperty(prefix+"revision","0");
        commit(next); // Node event revision is separate from semantic goal revision.
    }
    public synchronized void observeNode(String id, String status) {
        open();
        String prefix="node."+id+".";
        if (!state.containsKey(prefix+"status") || !Set.of("completed","failed","waiting","unknown").contains(status))
            throw new IllegalArgumentException("Unknown node or invalid observed result");
        String prior=state.getProperty(prefix+"status");
        if (Set.of("completed","failed").contains(prior) && !prior.equals(status))
            throw new IllegalStateException("Conflicting terminal node result");
        if(prior.equals(status)) return;
        var next=copy();next.setProperty(prefix+"status",status);
        next.setProperty(prefix+"revision",""+Math.addExact(Long.parseLong(state.getProperty(prefix+"revision")),1));
        commit(next);
    }
    public synchronized Map<String,Object> snapshot(long now) {
        open(); var result = new LinkedHashMap<String,Object>();
        result.put("episode_id", state.getProperty("episode"));
        result.put("revision", revision()); result.put("calls", modelCalls());
        result.put("model_calls_by_layer", Map.of("judgment",Long.parseLong(state.getProperty("calls.judgment","0")),
            "execution",Long.parseLong(state.getProperty("calls.execution","0")),"user",Long.parseLong(state.getProperty("calls.user","0"))));
        result.put("deadline", deadline()); result.put("can_dispatch", canDispatch(now));
        boolean stopped = Boolean.parseBoolean(state.getProperty("stopped"));
        result.put("episode_status", stopped ? "stopped" : "running");
        result.put("stop_reason", state.getProperty("stopReason", ""));
        result.put("resumes", Long.parseLong(state.getProperty("resumes", "0")));
        result.put("latest", state.getProperty("latest", ""));
        result.put("input_status", state.getProperty("inputStatus", "none"));
        var goals = new ArrayList<Map<String,Object>>();
        for (String id : goalIds()) goals.add(Map.of("goal_id",id,"episode_id",state.getProperty("episode"),
            "description",state.getProperty("goal."+id+".description"),"state",goalState(id),
            "waiting_for",state.getProperty("goal."+id+".waiting", ""),
            "waiting_kind",state.getProperty("goal."+id+".waitingKind", ""),
            "outcome",state.getProperty("goal."+id+".outcome", "undetermined"),
            "requirements",state.getProperty("goal."+id+".requirements", ""),
            "dependencies",dependencies(id)));
        String outcome = "undetermined";
        if (!goals.isEmpty() && goals.stream().allMatch(g -> "closed".equals(g.get("state")))) {
            if (goals.stream().allMatch(g -> "success".equals(g.get("outcome")))) outcome = "success";
            else if (goals.stream().anyMatch(g -> "unknown".equals(g.get("outcome")))) outcome = "unknown";
            else if (goals.stream().anyMatch(g -> "success".equals(g.get("outcome")))) outcome = "partial";
            else if (goals.stream().allMatch(g -> "cancelled".equals(g.get("outcome")))) outcome = "cancelled";
            else outcome = "failed";
        }
        if (stopped && "undetermined".equals(outcome))
            outcome = goals.stream().anyMatch(g -> "success".equals(g.get("outcome"))) ? "partial" : "unknown";
        result.put("outcome", outcome);
        var nodes=new ArrayList<Map<String,String>>();
        for(String key:new TreeSet<>(state.stringPropertyNames())) {
            if(key.startsWith("node.") && key.endsWith(".status")) {
                String id=key.substring(5,key.length()-7),prefix="node."+id+".";
                nodes.add(Map.of("node_id",id,"goal_id",state.getProperty(prefix+"goal"),"kind",state.getProperty(prefix+"kind"),
                    "status",state.getProperty(key),"decision_ref",state.getProperty(prefix+"decision")));
            }
        }
        result.put("nodes",nodes);
        result.put("goals", goals);
        var unresolved = new ArrayList<Map<String,String>>();
        for (String key : new TreeSet<>(state.stringPropertyNames())) {
            if (key.startsWith("event.") && key.endsWith(".status") && "clarify".equals(state.getProperty(key))) {
                String message = new String(Base64.getUrlDecoder().decode(key.substring(6,key.length()-7)),java.nio.charset.StandardCharsets.UTF_8);
                unresolved.add(Map.of("message_id",message,"content",state.getProperty(eventKey(message)+".content")));
            }
        }
        result.put("unresolved_inputs", unresolved); return result;
    }
    public synchronized String messageStatus(String message) {
        open(); return state.getProperty(eventKey(message)+".status", "absent");
    }
    public synchronized void social(String message, long revision) {
        input(message, revision);
        var next = copy(); next.setProperty(eventKey(message)+".status", "applied");
        next.setProperty("inputStatus", "applied");
        // Social input cannot silently resume old work or clear clarification.
        next.setProperty("blocked", "true"); revise(next);
    }
    public synchronized List<String> goalIds() {
        open(); var ids = new ArrayList<String>();
        for (int i=0; i<number("goals"); i++) ids.add(state.getProperty("goalIndex."+i));
        return List.copyOf(ids);
    }
    public synchronized String goalState(String id) {
        open(); String value = state.getProperty("goal."+id+".state");
        if (value == null) throw new IllegalArgumentException("Unknown goal"); return value;
    }
    /** Necessary input/task condition only; Hub must independently authorize each operation. */
    public synchronized boolean canDispatch(long now) {
        open();
        return !Boolean.parseBoolean(state.getProperty("stopped"))
            && !Boolean.parseBoolean(state.getProperty("blocked")) && now >= 0 && now < deadline()
            && modelCalls() < number("callLimit")
            && goalIds().stream().anyMatch(id -> "active".equals(goalState(id)));
    }
    public synchronized void chargeModelCall(long now) {
        chargeModelCall(now, "judgment");
    }
    public synchronized void chargeModelCall(long now, String kind) {
        active();
        if (!Set.of("judgment", "execution", "user").contains(kind)) throw new IllegalArgumentException("Unknown model layer");
        long layerCalls = Long.parseLong(state.getProperty("calls."+kind, "0"));
        if ("judgment".equals(kind) && layerCalls >= 64) throw new IllegalStateException("Judgment budget exhausted");
        if (now < 0 || now >= deadline() || modelCalls() >= number("callLimit"))
            throw new IllegalStateException("Budget exhausted");
        var next = copy(); next.setProperty("calls", ""+Math.addExact(modelCalls(), 1));
        next.setProperty("calls."+kind, ""+Math.addExact(layerCalls, 1)); revise(next);
    }
    public synchronized void stop(String reason) {
        open(); requireText(reason); var next = copy();
        next.setProperty("stopped", "true"); next.setProperty("stopReason", reason); revise(next);
    }
    private void release() {
        try { if (lock != null) lock.close(); } catch (IOException ignored) { }
        try { if (lockChannel != null) lockChannel.close(); } catch (IOException ignored) { }
    }
    @Override public synchronized void close() { closed = true; release(); }
}
