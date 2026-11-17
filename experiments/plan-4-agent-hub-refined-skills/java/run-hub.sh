#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
repo_root="$(cd ../../.. && pwd)"
exec "${JAVA_HOME:+$JAVA_HOME/bin/}java" -cp "target/runtime:$repo_root/shared/java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.HubDeepAgentBridge
