package eval;
import java.util.Map;
public final class BridgeErrorSelfTest {
 public static void main(String[] args) {
  var context=new ObservedToolContext();
  var failed=DeepAgentBridge.officialResult(context,"one","read",Map.of(),Map.of("type","tool_result","tool_call_id","one","content","official failure","error",true));
  if(!Boolean.FALSE.equals(failed.get("success")) || !"OFFICIAL_TOOL_ERROR".equals(failed.get("error")))throw new AssertionError("Failure hidden");
  if(!context.contextText().contains("official failure"))throw new AssertionError("Failure content lost");
  var ok=DeepAgentBridge.officialResult(context,"two","read",Map.of(),Map.of("type","tool_result","tool_call_id","two","content","observed success","error",false));
  if(!Boolean.TRUE.equals(ok.get("success")))throw new AssertionError("Success lost");
  try {DeepAgentBridge.officialResult(context,"three","read",Map.of(),Map.of("type","tool_result","tool_call_id","other","content","wrong"));throw new AssertionError("Mismatched identity accepted");}
  catch(IllegalArgumentException expected) { }
  if(!"completion_timeout".equals(DeepAgentBridge.finalError(Map.of("output",Map.of("final_result",Map.of("error","completion_timeout"))))))throw new AssertionError("Nested Core error hidden");
  if(DeepAgentBridge.finalError(Map.of("output","normal"))!=null)throw new AssertionError("Normal answer rejected");
  System.out.println("PASS failure propagation, observed content preservation, success, mismatched call rejection; model_calls=0");
 }
}
