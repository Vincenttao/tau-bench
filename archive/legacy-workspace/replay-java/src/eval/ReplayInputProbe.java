package eval;
import com.moaagent.agent.skill.*;
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
import java.util.concurrent.atomic.AtomicInteger;
/** Inspect actual pre-client model content, without any external model call. */
public final class ReplayInputProbe {
 public static void main(String[] args) throws Exception {
  try {
   CheckpointerFactory.setDefaultCheckpointer(new InMemoryCheckpointer());Runner.setConfig(RunnerConfig.DEFAULT);
   Path out=Path.of(args[0]);Files.createDirectories(out);
   Path root=Files.createTempDirectory("replay-input-probe-");Files.createDirectories(root.resolve("entry"));
   Files.writeString(root.resolve("entry/SKILL.md"),"---\nname: entry\ndescription: Replay input fixture\n---\nThis is synthetic probe data.\n");
   var calls=new AtomicInteger();
   var model=new Model(new Model.ModelClient() {
    AssistantMessageChunk answer(List<BaseMessage> messages) {
     calls.incrementAndGet();var content=messages.stream().map(message->Map.of("role",message.getRole(),"content",String.valueOf(message.getContent()))).toList();
     try {Files.writeString(out.resolve("model-content.json"),Json.write(content));Files.writeString(out.resolve("status.json"),Json.write(Map.of("model_request_count",calls.get(),"dynamic_fixture_path_present",content.stream().anyMatch(m->m.get("content").contains(root.toString())),"fixture_root",root.toString(),"gateway_model_calls",0,"scope","Actual NativeSkillAgent pre-client content only; not a complete bank replay")));}
     catch(Exception ex){throw new IllegalStateException(ex);}
     var chunk=new AssistantMessageChunk();chunk.setContent("Local probe complete.");return chunk;
    }
    public CompletionStage<AssistantMessage> invoke(List<BaseMessage> messages,ModelInvokeOptions options){return CompletableFuture.completedFuture(answer(messages));}
    public Iterator<AssistantMessageChunk> stream(List<BaseMessage> messages,ModelInvokeOptions options){return List.of(answer(messages)).iterator();}
   });
   var agent=NativeSkillAgent.create(new NativeSkillAgent.Settings("fixed-probe-agent",root.resolve("workspace").toString(),2,"Return a short answer."),model,new SkillAssets(root.toString(),"entry"),Map.of(),(session,source,input)->Map.of());
   agent.deepConfig().setCompletionTimeout(10.0);
   var stream=agent.stream(Map.of("query","Inspect initial input","conversation_id","fixed-probe-agent"),AgentSession.createAgentSession("fixed-probe-agent",null,agent.getCard()),List.of(StreamMode.OUTPUT));while(stream.hasNext())stream.next();
   if(calls.get()==0)throw new AssertionError("No actual model boundary entered");
   System.out.println(Files.readString(out.resolve("status.json")));
  }finally{Runner.stop();}
 }
}
