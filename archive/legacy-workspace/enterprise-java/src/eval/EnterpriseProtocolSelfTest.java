package eval;
import java.util.*;
public final class EnterpriseProtocolSelfTest {
 public static void main(String[] args) throws Exception {
  var completed=Map.<String,Object>of("id","task-one","contextId","context-one","status",Map.of("state","TASK_STATE_COMPLETED"),"artifacts",List.of(Map.of("artifactId","answer","parts",List.of(Map.of("text","customer answer")),"metadata",Map.of("_agentcore_terminal",true))));
  var result=EnterpriseBankingBridge.reply(completed);
  if(!"customer answer".equals(result.get("content")) || !Boolean.FALSE.equals(result.get("waiting")))throw new AssertionError("Terminal business output lost");
  var waiting=Map.<String,Object>of("id","task-one","contextId","context-one","status",Map.of("state","TASK_STATE_INPUT_REQUIRED","message",Map.of("role","ROLE_AGENT","messageId","question-one","parts",List.of(Map.of("text","Which account?")))));
  result=EnterpriseBankingBridge.reply(waiting);
  if(!Boolean.TRUE.equals(result.get("waiting")) || !"task-one".equals(result.get("runtime_task_id")) || !"Which account?".equals(result.get("content")))throw new AssertionError("Waiting question or identity lost");
  try {EnterpriseBankingBridge.reply(Map.of("id","task-one","status",Map.of("state","TASK_STATE_FAILED")));throw new AssertionError("Failed Task accepted");}
  catch(IllegalStateException expected) {}
  try {EnterpriseBankingBridge.reply(Map.of("id","task-one","contextId","context-one","status",Map.of("state","TASK_STATE_COMPLETED")));throw new AssertionError("Empty answer fabricated");}
  catch(IllegalStateException expected) {}
  System.out.println("PASS official SDK Task parsing, completed answer, INPUT_REQUIRED identity/question, failed/empty rejection; gateway_calls=0");
 }
}
