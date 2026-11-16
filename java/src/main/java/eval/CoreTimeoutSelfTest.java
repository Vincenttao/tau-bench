package eval;

import com.moaagent.agent.skill.*;
import com.moaagent.agent.interaction.narration.ProgressNarrationCoordinator;
import com.openjiuwen.core.foundation.llm.Model;
import com.openjiuwen.core.foundation.llm.ModelInvokeOptions;
import com.openjiuwen.core.foundation.llm.schema.AssistantMessage;
import com.openjiuwen.core.foundation.llm.schema.*;
import com.openjiuwen.core.runner.Runner;
import com.openjiuwen.core.runner.RunnerConfig;
import com.openjiuwen.core.session.AgentSession;
import com.openjiuwen.core.session.checkpointer.*;
import com.openjiuwen.core.session.stream.*;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;

/** Real Core deadline with a deliberately unfinished local model; no network calls. */
public final class CoreTimeoutSelfTest {
 public static void main(String[] args) throws Exception {
  var pending=new CompletableFuture<AssistantMessage>();
  var calls=new AtomicInteger();
  try {
   CheckpointerFactory.setDefaultCheckpointer(new InMemoryCheckpointer());
   Runner.setConfig(RunnerConfig.DEFAULT);
   var root=Files.createTempDirectory("core-timeout-test-");
   Files.createDirectories(root.resolve("entry"));
   Files.writeString(root.resolve("entry/SKILL.md"),"---\nname: entry\ndescription: Timeout test\n---\nRespond briefly.\n");
   var model=new Model(new Model.ModelClient() {
    public java.util.concurrent.CompletionStage<AssistantMessage> invoke(List<BaseMessage> messages,ModelInvokeOptions options) {calls.incrementAndGet();return pending;}
    public Iterator<AssistantMessageChunk> stream(List<BaseMessage> messages,ModelInvokeOptions options) {
     calls.incrementAndGet();
     return new Iterator<>() {
      public boolean hasNext(){pending.join();return false;}
      public AssistantMessageChunk next(){throw new NoSuchElementException();}
     };
    }
   });
   var agent=NativeSkillAgent.create(new NativeSkillAgent.Settings("deadline-test",root.resolve("workspace").toString(),2,"Respond briefly."),model,new SkillAssets(root.toString(),"entry"),Map.of(),new NativeSkillAgent.ExecutionServices((session,source,input)->Map.of(),ProgressNarrationCoordinator.disabled(),(session,event,payload)->{},List.of(),new ObservedToolContext()));
   agent.deepConfig().setCompletionTimeout(1.0);
   long started=System.nanoTime(); String error=null;
   var stream=agent.stream(Map.of("query","hello","conversation_id","deadline-test"),AgentSession.createAgentSession("deadline-test",null,agent.getCard()),List.of(StreamMode.OUTPUT));
   while(stream.hasNext()) {
    Object item=stream.next();
    if(item instanceof OutputSchema output) {
     String found=Tau2Bridge.finalError(output.getPayload());
     if(found!=null)error=found;
    }
   }
   double elapsed=(System.nanoTime()-started)/1e9;
   if(!"completion_timeout".equals(error))throw new AssertionError("Expected completion_timeout, got "+error);
   if(calls.get()==0)throw new AssertionError("Model was not entered");
   if(elapsed>20)throw new AssertionError("Deadline not bounded: "+elapsed);
   System.out.println("PASS actual Core deadline; error="+error+"; elapsed_seconds="+elapsed+"; local_invocations="+calls+"; gateway_calls=0");
  } finally {pending.complete(new AssistantMessage("finished"));Runner.stop();}
 }
}
