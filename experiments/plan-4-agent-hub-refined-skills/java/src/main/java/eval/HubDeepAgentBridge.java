package eval;

import com.moaagent.agent.skill.*;
import com.moaagent.agent.support.Json;
import com.moaagent.agent.interaction.narration.ProgressNarrationCoordinator;
import com.openjiuwen.core.foundation.llm.Model;
import com.openjiuwen.core.foundation.llm.schema.*;
import com.openjiuwen.core.runner.Runner;
import com.openjiuwen.core.runner.RunnerConfig;
import com.openjiuwen.core.session.AgentSession;
import com.openjiuwen.core.session.checkpointer.*;
import com.openjiuwen.core.session.interaction.*;
import com.openjiuwen.core.session.stream.*;
import com.openjiuwen.harness.deep_agent.DeepAgent;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Evaluation-only transport adapter. Never executes a tau2 business tool locally. */
public final class HubDeepAgentBridge {
  static final BufferedReader IN = new BufferedReader(new InputStreamReader(System.in));
  static final PrintStream OUT = System.out;
  static String waitingId;
  static String question;
  static long calls;
  static final java.util.concurrent.ExecutorService CONTROL_READER = java.util.concurrent.Executors.newSingleThreadExecutor(r -> {var t=new Thread(r,"hub-control-input");t.setDaemon(true);return t;});
  static synchronized void control(String method, Object data) {
    String requestId=UUID.randomUUID().toString();
    emit(Map.of("type","control_request","id",requestId,"method",method,"data",data));
    try {
      var reply=CONTROL_READER.submit(() -> read()).get(30,java.util.concurrent.TimeUnit.SECONDS);
      if(!"control_response".equals(reply.get("type")) || !requestId.equals(reply.get("id")) || !Boolean.TRUE.equals(reply.get("ok")))
        throw new IllegalStateException("Control reservation refused");
    } catch(Exception error) {throw new IllegalStateException("Hub control unavailable; model execution stopped",error);}
  }
  static Map<String,Object> read() throws IOException {
    String line=IN.readLine(); if(line==null) throw new EOFException("Host disconnected");
    return Json.object(line);
  }
  static synchronized void emit(Map<String,Object> msg) { OUT.println("TAU2_JSON:"+Json.write(msg)); OUT.flush(); }
  static String env(String k,String d) { return System.getenv().getOrDefault(k,d); }
  static ModelClientConfig modelClientConfig(String key, String base, double timeout) {
    return ModelClientConfig.builder().clientProvider("OpenAI").apiKey(key).apiBase(base)
        .timeout(timeout).maxRetries(0).build();
  }
  static Map<String,Object> resultSchema() { return Map.of("type","object","properties",Map.of("result",Map.of("type","string")),"required",List.of("result"),"additionalProperties",false); }
  static Map<String,Object> officialResult(ObservedToolContext observedContext,String callId,String name,Object arguments,Map<String,Object> result) {
        if(!"tool_result".equals(result.get("type")) || !callId.equals(result.get("tool_call_id"))) throw new IllegalArgumentException("Mismatched tool result");
        var data=observedContext.observe(callId,name,arguments,String.valueOf(result.get("content")));
        if (Boolean.TRUE.equals(result.get("error"))) {
          return Map.of("success",false,"error","OFFICIAL_TOOL_ERROR","data",data,"model_data",data);
        }
        return Map.of("success",true,"data",data,"model_data",data);
  }
  static String finalError(Object value) {
    if (!(value instanceof Map<?,?> map)) return null;
    if (map.get("error") instanceof String error && !error.isBlank()) return error;
    for (String key : List.of("final_result", "output")) {
      String nested=finalError(map.get(key)); if(nested!=null) return nested;
    }
    if(map.get("rounds") instanceof List<?> rounds && !rounds.isEmpty()) return finalError(rounds.get(rounds.size()-1));
    return null;
  }
  public static void main(String[] args) throws Exception {
    // Library logging goes to stderr, leaving a framed stdout protocol.
    System.setOut(System.err);
    try { run(); } catch(Throwable e) { e.printStackTrace(System.err); emit(Map.of("type","error","error",e.toString())); System.exit(1); }
    finally { Runner.stop(); }
  }
  @SuppressWarnings("unchecked") static void run() throws Exception {
    var init=read(); if(!"session_init".equals(init.get("type"))) throw new IllegalArgumentException("Expected session_init");
    var history=(List<?>)init.getOrDefault("messages",List.of());
    if(history.stream().anyMatch(x -> !(x instanceof Map<?,?> m) || !Set.of("system","user","assistant").contains(m.get("role")) || (m.get("tool_calls") != null && (!(m.get("tool_calls") instanceof List<?> calls) || !calls.isEmpty()))))
      throw new IllegalArgumentException("Initial tool interactions are not supported");
    var priorHistory=history.stream().filter(x -> !"system".equals(((Map<?,?>)x).get("role"))).toList();
    boolean firstUser=true;
    Path waitFile=Path.of(String.valueOf(init.get("workspace"))).resolve("waiting.json");
    if(Files.exists(waitFile)) {
      var saved=Json.object(Files.readString(waitFile));waitingId=(String)saved.get("waiting_id");question=(String)saved.get("question");
    }
    CheckpointerFactory.setDefaultCheckpointer(CheckpointerFactory.create("persistence",Map.of("db_type","shelve","db_path",Path.of(String.valueOf(init.get("workspace"))).resolve("checkpoints").toString()))); Runner.setConfig(RunnerConfig.DEFAULT);
    String id=String.valueOf(init.get("session_id"));
    var model=new Model(modelClientConfig(env("OPENAI_API_KEY",""),env("OPENAI_BASE_URL",""),
        Double.parseDouble(env("MODEL_REQUEST_TIMEOUT_SECONDS","120"))),ModelRequestConfig.builder().temperature(0.0).topP(1.0).modelName(String.valueOf(init.get("model"))).build());
    try (var assembly=new HubDeepAgentAssembly(init,model)) {
    DeepAgent agent=assembly.agent;
    agent.deepConfig().setCompletionTimeout(Double.parseDouble(env("JAVA_AGENT_COMPLETION_TIMEOUT","600")));
    emit(Map.of("type","ready","implementation","Hub-Controlled-DeepAgent","checkpoint","shelve"));
    while(true) {
      var request=read(); if("close".equals(request.get("type"))) return;
      if(!Set.of("user", "controller_review").contains(request.get("type"))) throw new IllegalArgumentException("Expected user or controller review event");
      Object query=String.valueOf(request.get("content"));
      if(firstUser && !priorHistory.isEmpty()) {
        query="The following JSON is prior conversation history, not new instructions. Preserve its roles when interpreting it.\n<prior_conversation>\n"+Json.write(priorHistory)+"\n</prior_conversation>\nCurrent user message:\n"+query;
      }
      firstUser=false;
      if(waitingId!=null) {
        var resume=new InteractiveInput();
        resume.update(waitingId,ControllerAskUserRail.resumeValue(String.valueOf(request.get("type")),String.valueOf(query)));
        query=resume;
      }
      waitingId=null; question=null; assembly.question=null; String answer="";
      var stream=agent.stream(Map.of("query",query,"conversation_id",id),AgentSession.createAgentSession(id,null,agent.getCard()),List.of(StreamMode.OUTPUT));
      while(stream.hasNext()) {
        Object chunk=stream.next();
        if(chunk instanceof OutputSchema s) {
          if(s.getPayload() instanceof InteractionOutput io) { waitingId=io.getId(); if(question==null) question=Json.write(io.getValue()); }
          else if(Set.of("answer","error").contains(s.getType()) && s.getPayload() instanceof Map<?,?> p) {
            if("error".equals(s.getType())) throw new IllegalStateException("Core stream error: "+p.get("output"));
            String coreError=finalError(p);
            if(coreError!=null) throw new IllegalStateException("Core execution error: "+coreError);
            Object output=p.get("output");
            if(output instanceof Map<?,?> m && m.get("output")!=null) answer=String.valueOf(m.get("output"));
            else if(output instanceof String text) answer=text;
          }
        }
      }
      if(assembly.transportFailure!=null) throw assembly.transportFailure;
      if(assembly.question!=null) question=assembly.question;
      if(waitingId!=null) answer=question==null?"Please provide the requested information.":question;
      if(answer.isBlank()) throw new IllegalStateException("No user-visible output from DeepAgent");
      var waiting = new LinkedHashMap<String,Object>();waiting.put("waiting_id",waitingId);waiting.put("question",question);
      Path temporary=waitFile.resolveSibling("waiting.tmp");Files.writeString(temporary,Json.write(waiting));
      Files.move(temporary,waitFile,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
      emit(Map.of("type","content","content",answer,"waiting",waitingId!=null));
    }
  }
  }
}
