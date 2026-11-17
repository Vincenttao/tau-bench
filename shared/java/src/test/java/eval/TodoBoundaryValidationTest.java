package eval;

import java.util.*;

/** Regression coverage for model-generated Todo batches before they reach Core/A2A. */
public final class TodoBoundaryValidationTest {
    public static void main(String[] args) {
        var existing=Map.of("identity","in_progress","sequencing","pending");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("status","completed"))),existing,"non-empty id");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("id","provisional_credit","status","pending"))),existing,"unknown id");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of("id","sequencing","status","pending"))),existing,"existing id");
        var newItem=Map.<String,Object>of("id","new","status","pending","content","New check",
                "activeForm","Checking","description","Evidence required");
        expectInvalid(Map.of("action","append","todos",List.of(newItem,newItem)),existing,"duplicate id");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of("id","new"))),existing,"explicit status");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of(
                "id","new","status","pending","description","source","activeForm","Checking"))),existing,"content");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("id","sequencing","status","in_progress"))),existing,"items in_progress");
        expectValid(Map.of("action","update","todos",List.of(Map.of("id","identity","status","completed"))),existing);
        expectValid(Map.of("action","update","todos",List.of(
                Map.of("id","identity","status","completed"),
                Map.of("id","sequencing","status","in_progress"))),existing);
        expectValid(Map.of("action","append","todos",List.of(Map.of(
                "id","provisional_credit","status","pending","content","Check provisional credit",
                "activeForm","Checking provisional credit","description","Policy evidence required"))),existing);
        var decoded=DeepAgentAssembly.decodeToolArgs("{\"action\":\"update\",\"todos\":[{\"id\":\"identity\"}]}" );
        expectInvalid(decoded,existing,"explicit status");
        if(!DeepAgentAssembly.todoCallSucceeded(Map.of("message","Successfully updated 1 task(s)")))
            throw new AssertionError("Successful Todo result was not recognized");
        if(DeepAgentAssembly.todoCallSucceeded(""))
            throw new AssertionError("Empty failed Todo result was recognized as success");
        System.out.println("PASS Todo boundary rejects invalid ids, missing status and multiple in_progress before Core/A2A");
    }

    private static void expectInvalid(Map<String,Object> args,Map<String,String> state,String fragment) {
        var error=DeepAgentAssembly.validateTodoModify(args,state);
        if(error.isEmpty() || !error.get().contains(fragment))
            throw new AssertionError("Expected error containing '"+fragment+"' but got "+error);
    }

    private static void expectValid(Map<String,Object> args,Map<String,String> state) {
        var error=DeepAgentAssembly.validateTodoModify(args,state);
        if(error.isPresent()) throw new AssertionError("Unexpected validation error: "+error.get());
    }
}
