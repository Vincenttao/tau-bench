#!/usr/bin/env bash
set -euo pipefail
SCRIPT_FILE="$(readlink -f "$0")"
cd "$(dirname "$SCRIPT_FILE")/../../../java"
JAVA_BIN="${JAVA_HOME:+$JAVA_HOME/bin/}java"
exec "$JAVA_BIN" -cp "target/classes:$(cat classpath.txt)" eval.DeepAgentBridge
