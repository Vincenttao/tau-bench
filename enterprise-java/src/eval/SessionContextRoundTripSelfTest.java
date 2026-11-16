package eval;

import com.moaagent.agent.skill.*;
import com.moaagent.agent.interaction.narration.ProgressNarrationCoordinator;
import com.moaagent.agent.support.Json;
import com.openjiuwen.core.foundation.llm.*;
import com.openjiuwen.core.foundation.llm.schema.*;
import com.openjiuwen.core.runner.*;
import com.openjiuwen.core.session.AgentSession;
import com.openjiuwen.core.session.checkpointer.*;
import com.openjiuwen.core.session.stream.StreamMode;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Actual NativeSkillAgent read/tool/model round trip, scripted local responses. */
public final class SessionContextRoundTripSelfTest {
 public static void main(String[] args) throws Exception {
  try {
   CheckpointerFactory.setDefaultCheckpointer(new InMemoryCheckpointer());Runner.setConfig(RunnerConfig.DEFAULT);
   var root=Files.createTempDirectory("session-context-roundtrip-");Files.createDirectories(root.resolve("entry"));
   Files.writeString(root.resolve("entry/SKILL.md"),"---\nname: entry\ndescription: Local context test\n---\nRead the probe tool once.\n");
   Files.writeString(root.resolve("probe.py"),"# local fixture, never executed as Python");
   var observed=new SessionObservedToolContext();var calls=new AtomicInteger();var seen=new AtomicBoolean();
   String data="FULL_MODEL_OBSERVATION_"+"x".repeat(100000);
   var model=new Model(new Model.ModelClient() {
    AssistantMessageChunk response(List<BaseMessage> messages) {
     int call=calls.incrementAndGet();var chunk=new AssistantMessageChunk();chunk.setRole("assistant");chunk.setContent("");
     if(call==1)chunk.setToolCalls(List.of(ToolCall.builder().id("read-call").name("read_file").arguments(Json.write(Map.of("file_path","entry/SKILL.md"))).build()));
     else if(call==2)chunk.setToolCalls(List.of(ToolCall.builder().id("probe-call").name("call_mcp").arguments(Json.write(Map.of("operation","probe","arguments",Map.of("arguments_json","{}")))).build()));
     else {
      seen.set(messages.stream().anyMatch(m->m instanceof UserMessage u && u.getContentAsString().contains(data)));
      if(!seen.get())throw new AssertionError("Actual next model request lost session tool data");
      chunk.setContent("Probe complete.");
     }
     return chunk;
    }
    public CompletionStage<AssistantMessage> invoke(List<BaseMessage> messages,ModelInvokeOptions options){return CompletableFuture.completedFuture(response(messages));}
    public Iterator<AssistantMessageChunk> stream(List<BaseMessage> messages,ModelInvokeOptions options){return List.of(response(messages)).iterator();}
   });
   var schema=Map.<String,Object>of("type","object","properties",Map.of("arguments_json",Map.of("type","string")),"required",List.of("arguments_json"),"additionalProperties",false);
   var operation=new SkillOperation(SkillOperation.Type.SCRIPT,"Probe",null,null,null,null,"probe.py",schema,Tau2Bridge.resultSchema(),Map.of(),false,false,2,null,Map.of(),Map.of(),false,null,Tau2Bridge.resultSchema());
   SkillScriptRunner scripts=(session,source,input)->{
    var receipt=observed.observe(session,"probe-call","probe",Map.of(),data);
    return Map.of("success",true,"data",receipt,"model_data",receipt);
   };
   var agent=NativeSkillAgent.create(new NativeSkillAgent.Settings("context-roundtrip",root.resolve("workspace").toString(),5,"Read entry/SKILL.md, call probe, then finish."),model,new SkillAssets(root.toString(),"entry"),Map.of("probe",operation),new NativeSkillAgent.ExecutionServices(scripts,ProgressNarrationCoordinator.disabled(),(session,event,payload)->{},List.of(),observed));
   agent.deepConfig().setCompletionTimeout(15.0);
   var stream=agent.stream(Map.of("query","Run the local probe","conversation_id","context-roundtrip"),AgentSession.createAgentSession("context-roundtrip",null,agent.getCard()),List.of(StreamMode.OUTPUT));
   while(stream.hasNext())stream.next();
   if(!seen.get() || calls.get()!=3)throw new AssertionError("Unexpected round trip: model invocations="+calls+", data seen="+seen);
   System.out.println("PASS actual NativeSkillAgent read_file -> call_mcp -> next model input contains full100k session data; local_model_invocations="+calls+"; gateway_calls=0");
  } finally {Runner.stop();}
 }
}
