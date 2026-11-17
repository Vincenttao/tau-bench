#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gate_root="$PWD"
repo_root="$(cd ../../.. && pwd)"
hub_root="${AGENT_HUB_ROOT:-$repo_root/../agent-hub-alpha}"
go_bin="${GO_BIN:-$repo_root/.deps/toolchains/go/bin/go}"
export GOCACHE="${GOCACHE:-/tmp/tau3-go-cache}"
export GOMODCACHE="${GOMODCACHE:-/tmp/tau3-go-mod}"
mkdir -p target
python check_source.py
"$go_bin" test -mod=readonly -c -o target/gate.test .
"$go_bin" build -mod=readonly -o target/banking-gate ./cmd/banking-gate
# Upstream schema discovery is relative to CWD; keep source/schema bytes untouched.
cd "$hub_root/agent-festival/schema"
"$gate_root/target/gate.test" -test.v
