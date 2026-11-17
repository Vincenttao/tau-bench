package eval;
import com.moaagent.agent.support.Json;
import com.moaagent.agent.skill.SkillSchema;
import com.moaagent.agent.routing.context.ModelContextContributor;
import com.openjiuwen.core.singleagent.rail.ModelCallInputs;
import com.openjiuwen.core.foundation.llm.schema.UserMessage;
import java.nio.file.*;
import java.util.*;
public final class ContextSelfTest {
 public static void main(String[] args) throws Exception {
  List<?> fixtures=Json.MAPPER.readValue(Files.readString(Path.of(args[0])),List.class);
  var cache=new ObservedToolContext(); var inputs=ModelCallInputs.builder().messages(List.of(new UserMessage("Current question"))).build();
  var expected=new ArrayList<Map<String,Object>>();int n=0;
  for(Object obj:fixtures) {
   var f=Json.object(obj);String content=(String)f.get("content");
   if(!ObservedToolContext.sha256(content).equals(f.get("sha256")))throw new AssertionError("Fixture hash mismatch");
   var receipt=cache.observe("call-"+(++n),"KB_search",Map.of("query",f.get("query")),content);
   SkillSchema.validate(Tau2Bridge.resultSchema(),receipt);
   if(Json.write(receipt).length()>8192)throw new AssertionError("Oversized summary");
   expected.add(f);
  }
  // Explicitly exercise beyond the product's 65536 raw-data ceiling without truncating.
  String large="NON_MODEL_SYNTHETIC_DATA_".repeat(4000);var receipt=cache.observe("large","size_test",Map.of(),large);
  SkillSchema.validate(Tau2Bridge.resultSchema(),receipt);
  cache.contribute(inputs,new ModelContextContributor.Context(null,"Current question",Map.of()));
  cache.contribute(inputs,new ModelContextContributor.Context(null,"Current question",Map.of()));
  if(inputs.getMessages().size()!=2)throw new AssertionError("Context block duplicated");
  String injected=((UserMessage)inputs.getMessages().get(1)).getContentAsString();
  List<?> observed=Json.MAPPER.readValue(injected.substring(injected.indexOf('\n',injected.indexOf('\n')+1)+1),List.class);
  if(observed.size()!=fixtures.size()+1)throw new AssertionError("Observations overwritten");
  for(int i=0;i<expected.size();i++) {
   var actual=Json.object(observed.get(i));var f=expected.get(i);
   if(!f.get("content").equals(actual.get("content")) || !f.get("sha256").equals(actual.get("sha256_utf8")))throw new AssertionError("Full text lost");
   System.out.println("KB_FULLTEXT_OK query="+f.get("query")+" characters="+((String)f.get("content")).length()+" sha256="+f.get("sha256"));
  }
  if(!large.equals(Json.object(observed.get(observed.size()-1)).get("content")))throw new AssertionError("Large result truncated");
  System.out.println("PASS observed="+observed.size()+" synthetic_characters="+large.length()+" model_input_characters="+injected.length()+" model_calls=0");
 }
}
