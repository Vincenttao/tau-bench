#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p replay-java/target/classes
"${JAVA_HOME:+$JAVA_HOME/bin/}javac" -parameters -cp "java/target/classes:$(cat java/classpath.txt)" -d replay-java/target/classes replay-java/src/eval/*.java
