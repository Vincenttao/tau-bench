package eval;

import java.util.*;

/** Regression coverage for model-generated Todo batches before they reach Core/A2A. */
public final class TodoBoundaryValidationTest {
    public static void main(String[] args) {
        var existing=Map.of("identity","in_progress","sequencing","pending");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("status","completed"))),existing,"non-empty id");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("id","provisional_credit","status","pending"))),existing,"unknown id");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of("id","sequencing","status","pending"))),existing,"existing id");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of("id","new","status","pending"),Map.of("id","new","status","pending"))),existing,"duplicate id");
        expectInvalid(Map.of("action","append","todos",List.of(Map.of("id","new"))),existing,"explicit status");
        expectInvalid(Map.of("action","update","todos",List.of(Map.of("id","sequencing","status","in_progress"))),existing,"items in_progress");
        expectValid(Map.of("action","update","todos",List.of(Map.of("id","identity","status","completed"))),existing);
        expectValid(Map.of("action","update","todos",List.of(
                Map.of("id","identity","status","completed"),
                Map.of("id","sequencing","status","in_progress"))),existing);
        expectValid(Map.of("action","append","todos",List.of(Map.of("id","provisional_credit","status","pending"))),existing);
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
