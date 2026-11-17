#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
repo_root="$(cd ../../.. && pwd)"
mkdir -p target/task-host
javac --release 17 -cp "$(cat "$repo_root/shared/java/classpath.txt")" -d target/task-host src/main/java/eval/hub/TaskCoordinator.java src/main/java/eval/hub/TaskHost.java
