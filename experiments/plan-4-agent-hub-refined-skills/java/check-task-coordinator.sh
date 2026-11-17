#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p target/task-contracts
javac --release 17 -d target/task-contracts src/main/java/eval/hub/TaskCoordinator.java src/test/java/eval/hub/TaskCoordinatorTest.java
java -cp target/task-contracts eval.hub.TaskCoordinatorTest
