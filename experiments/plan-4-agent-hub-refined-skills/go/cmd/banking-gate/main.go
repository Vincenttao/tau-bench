// banking-gate hosts the actual Hub adoption machine over a private stdio pipe.
// It is a transport component, not a substitute for the evidence/judgment workflow.
package main

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"

    gate "github.com/openjiuwen/agent-festival/go/banking-eval"
    "github.com/openjiuwen/agent-festival/go/internal/adopt"
    "github.com/openjiuwen/agent-festival/go/internal/ledger"
)

type request struct {
    ID string `json:"id"`
    Method string `json:"method"`
    Decision *adopt.Request `json:"decision"`
    Operation string `json:"operation"`
    Payload any `json:"payload"`
    Grants []ledger.Grant `json:"grants"`
    Success bool `json:"success"`
}

func main() {
    if len(os.Args) != 2 && len(os.Args) != 3 { fmt.Fprintln(os.Stderr, "usage: banking-gate LEDGER_PATH [READ_ONLY_POLICY]"); os.Exit(2) }
    var reads map[string]bool
    if len(os.Args) == 3 {
        data, err := os.ReadFile(os.Args[2])
        if err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
        var policy struct { Allowed []string `json:"allowed_read_operations"` }
        if json.Unmarshal(data, &policy) != nil || len(policy.Allowed) == 0 { os.Exit(1) }
        reads = map[string]bool{}
        for _, operation := range policy.Allowed { reads[operation] = true }
    }
    machine, err := gate.OpenGate(os.Args[1])
    if err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
    scanner := bufio.NewScanner(os.Stdin)
    scanner.Buffer(make([]byte, 4096), 1024*1024)
    encoder := json.NewEncoder(os.Stdout)
    for scanner.Scan() {
        var input request
        err := json.Unmarshal(scanner.Bytes(), &input)
        if err == nil && input.ID == "" { err = fmt.Errorf("missing request identity") }
        if err == nil && reads != nil && (input.Method == "decide" || input.Method == "dispatch") {
            payload, ok := input.Payload.(map[string]any)
            operation, _ := payload["operation"].(string)
            if !ok || !reads[operation] { err = fmt.Errorf("operation is outside the read-only pilot policy") }
        }
        if err == nil {
            switch input.Method {
            case "decide": err = machine.Decide(input.Decision, input.Payload)
            case "dispatch": err = machine.Dispatch(input.Operation, input.Payload, input.Grants)
            case "complete": err = machine.Complete(input.Operation, input.Success)
            default: err = fmt.Errorf("unknown gate method")
            }
        }
        response := map[string]any{"id": input.ID, "ok": err == nil, "component": "agent-hub/adopt"}
        if err != nil { response["error"] = err.Error() }
        if encoder.Encode(response) != nil { os.Exit(1) }
    }
    if scanner.Err() != nil { os.Exit(1) }
}
