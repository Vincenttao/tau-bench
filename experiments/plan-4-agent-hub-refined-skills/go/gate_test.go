package bankingeval

import (
    "path/filepath"
    "testing"

    "github.com/openjiuwen/agent-festival/go/internal/adopt"
    "github.com/openjiuwen/agent-festival/go/internal/ledger"
)

func request() *adopt.Request {
    return &adopt.Request{AdoptionVersion: "0.1.0",
        Identity: ledger.Identity{BusinessRequestID: "episode-one", OperationID: "operation-one"},
        Versions: ledger.Versions{Evidence: "evidence-one", Rule: "rule-one", Model: "model-one", Readout: "readout-one", Policy: "policy-one"},
        GrantsAtDecision: []ledger.Grant{{Kind: "data", Selector: "bank://account-one", Actions: []string{"write"}, Effect: "irreversible"}}}
}

func TestDispatchBindingAndUnknownRecovery(t *testing.T) {
    path := filepath.Join(t.TempDir(), "ledger.jsonl")
    gate, err := OpenGate(path)
    if err != nil { t.Fatal(err) }
    req := request()
    original := map[string]any{"amount": 100}
    if err := gate.Decide(req, original); err != nil { t.Fatal(err) }
    if err := gate.Dispatch(req.Identity.OperationID, map[string]any{"amount": 200}, req.GrantsAtDecision); err == nil {
        t.Fatal("changed payload was authorized")
    }
    if err := gate.Dispatch(req.Identity.OperationID, original, nil); err == nil { t.Fatal("revoked grant accepted") }
    if err := gate.Dispatch(req.Identity.OperationID, original, req.GrantsAtDecision); err != nil { t.Fatal(err) }
    if err := gate.Dispatch(req.Identity.OperationID, original, req.GrantsAtDecision); err == nil { t.Fatal("duplicate dispatch accepted") }
    // Crash after dispatch and before receipt: a restarted process must not issue a new effect.
    recovered, err := OpenGate(path)
    if err != nil { t.Fatal(err) }
    if err := recovered.Dispatch(req.Identity.OperationID, original, req.GrantsAtDecision); err == nil { t.Fatal("recovery duplicated an unknown effect") }
    if err := recovered.Complete(req.Identity.OperationID, true); err != nil { t.Fatal(err) }
}

func TestUnboundRequestRejected(t *testing.T) {
    gate, err := OpenGate(filepath.Join(t.TempDir(), "ledger.jsonl"))
    if err != nil { t.Fatal(err) }
    req := request()
    if err := gate.Dispatch(req.Identity.OperationID, map[string]any{}, req.GrantsAtDecision); err == nil {
        t.Fatal("dispatch without decision")
    }
    req.Versions.Evidence = ""
    if err := gate.Decide(req, map[string]any{}); err == nil { t.Fatal("missing evidence version accepted") }
}
