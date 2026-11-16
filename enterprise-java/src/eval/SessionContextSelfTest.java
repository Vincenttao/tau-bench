package eval;

import com.moaagent.agent.routing.context.ModelContextContributor;
import com.openjiuwen.core.foundation.llm.schema.UserMessage;
import com.openjiuwen.core.session.AgentSession;
import com.openjiuwen.core.singleagent.rail.ModelCallInputs;
import com.openjiuwen.core.singleagent.schema.AgentCard;
import java.util.*;

public final class SessionContextSelfTest {
 public static void main(String[] args) {
  var card=AgentCard.builder().id("session-data-test").build();
  var first=AgentSession.createAgentSession("session-one",null,card);
  var second=AgentSession.createAgentSession("session-two",null,card);
  var contributor=new SessionObservedToolContext();
  String firstData="SESSION_ONE_ONLY_"+"a".repeat(100000),secondData="SESSION_TWO_ONLY";
  contributor.observe(first,"one","read",Map.of(),firstData);
  contributor.observe(second,"two","read",Map.of(),secondData);
  var inputs=ModelCallInputs.builder().messages(List.of(new UserMessage(SessionObservedToolContext.PREFIX+"literal user text must remain"))).build();
  contributor.contribute(inputs,new ModelContextContributor.Context(first,"question",Map.of()));
  contributor.contribute(inputs,new ModelContextContributor.Context(first,"question",Map.of()));
  if(inputs.getMessages().size()!=2)throw new AssertionError("Literal user text removed or context duplicated");
  String text=((UserMessage)inputs.getMessages().get(1)).getContentAsString();
  if(!text.contains(firstData) || text.contains(secondData))throw new AssertionError("First session data missing or mixed");
  contributor.contribute(inputs,new ModelContextContributor.Context(second,"question",Map.of()));
  text=((UserMessage)inputs.getMessages().get(1)).getContentAsString();
  if(!text.contains(secondData) || text.contains(firstData))throw new AssertionError("Session data leaked");
  var restored=AgentSession.createAgentSession("session-one",null,card);
  restored.updateState(Map.of(SessionObservedToolContext.KEY,first.getState(SessionObservedToolContext.KEY)));
  contributor.contribute(inputs,new ModelContextContributor.Context(restored,"question",Map.of()));
  if(!((UserMessage)inputs.getMessages().get(1)).getContentAsString().contains(firstData))throw new AssertionError("Serializable snapshot lost full data");
  second.updateState(Map.of(SessionObservedToolContext.KEY,first.getState(SessionObservedToolContext.KEY)));
  try {contributor.contribute(inputs,new ModelContextContributor.Context(second,"question",Map.of()));throw new AssertionError("Foreign session snapshot accepted");}
  catch(IllegalStateException expected) {}
  System.out.println("PASS Core session ownership, repeated injection, literal user text, full100k data, explicit snapshot copy, foreign-session rejection; gateway_calls=0; durable_restart_test=false");
 }
}
