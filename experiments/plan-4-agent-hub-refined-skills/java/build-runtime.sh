#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
repo_root="$(cd ../../.. && pwd)"
bash build-task-host.sh
mkdir -p target/runtime
javac --release 17 -cp "$repo_root/shared/java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" -d target/runtime src/main/java/eval/InvocationSequence.java src/main/java/eval/TodoLimit.java src/main/java/eval/HubDeepAgentAssembly.java src/main/java/eval/HubDeepAgentBridge.java
javac --release 17 -cp target/runtime -d target/runtime src/test/java/eval/InvocationSequenceTest.java src/test/java/eval/TodoLimitTest.java
java -cp target/runtime eval.InvocationSequenceTest
java -cp target/runtime eval.TodoLimitTest
