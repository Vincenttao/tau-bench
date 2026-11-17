// Package bankingeval binds actual Hub adoption decisions to final dispatch payloads.
// This component is not yet wired to the live Python MCP effect boundary.
package bankingeval

import (
    "fmt"
    "sync"

    "github.com/openjiuwen/agent-festival/go/internal/adopt"
    "github.com/openjiuwen/agent-festival/go/internal/ledger"
)

type Gate struct {
    mu sync.Mutex
    machine *adopt.Machine
    digests map[string]string
}

func OpenGate(path string) (*Gate, error) {
    machine, err := adopt.Open(path)
    if err != nil { return nil, err }
    gate := &Gate{machine: machine, digests: map[string]string{}}
    events, err := machine.Events()
    if err != nil { return nil, err }
    for _, event := range events {
        if event.EventType == "adoption" && event.Outcome.Status == "adopted" && event.Idempotency != nil {
            gate.digests[event.Identity.OperationID] = event.Idempotency.PayloadDigest
        }
    }
    for op := range gate.digests {
        if machine.State(op) == adopt.StateDispatched {
            outcome := machine.MarkUnresolved(op)
            if outcome.Status != "unresolved" { return nil, fmt.Errorf("recovery: %s", outcome.Detail) }
        }
    }
    return gate, nil
}

// Decide accepts a trusted decision record; semantic evidence validation belongs to
// the upstream judgment/evidence workflow, not this transport binding component.
func (g *Gate) Decide(request *adopt.Request, payload any) error {
    g.mu.Lock()
    defer g.mu.Unlock()
    if request == nil { return fmt.Errorf("missing decision") }
    digest, err := adopt.Digest(payload)
    if err != nil { return err }
    copy := *request
    copy.PayloadDigest = digest
    outcome := g.machine.Adopt(&copy)
    if outcome.Status != "adopted" && outcome.Status != "reused" {
        return fmt.Errorf("adoption refused: %s", outcome.Detail)
    }
    g.digests[request.Identity.OperationID] = digest
    return nil
}

func (g *Gate) Dispatch(operation string, payload any, liveGrants []ledger.Grant) error {
    g.mu.Lock()
    defer g.mu.Unlock()
    digest, err := adopt.Digest(payload)
    if err != nil { return err }
    expected, exists := g.digests[operation]
    if !exists || digest != expected { return fmt.Errorf("payload has no matching decision") }
    outcome := g.machine.Dispatch(operation, liveGrants)
    if outcome.Status != "dispatched" { return fmt.Errorf("dispatch refused: %s", outcome.Detail) }
    return nil
}

func (g *Gate) Complete(operation string, success bool) error {
    g.mu.Lock()
    defer g.mu.Unlock()
    var outcome adopt.Outcome
    if success { outcome = g.machine.MarkCompleted(operation) } else { outcome = g.machine.MarkFailed(operation) }
    if outcome.Status != "completed" && outcome.Status != "failed" {
        return fmt.Errorf("receipt refused: %s", outcome.Detail)
    }
    return nil
}
