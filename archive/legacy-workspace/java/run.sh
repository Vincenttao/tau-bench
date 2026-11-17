#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
JAVA_BIN="${JAVA_HOME:+$JAVA_HOME/bin/}java"
exec "$JAVA_BIN" -cp "target/classes:$(cat classpath.txt)" eval.Tau2Bridge
